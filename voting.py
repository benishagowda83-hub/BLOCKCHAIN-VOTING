"""Blockchain Voting System - menu-driven console app.

Entities : Voter(voter_id, name, has_voted), Candidate(candidate_id, name)
Chain    : every admin action and every vote is a transaction stored in a block.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field

DIFFICULTY = 3  # number of leading zeros required in a block hash


# ----------------------------- Entities ------------------------------------
@dataclass
class Voter:
    voter_id: str
    name: str
    has_voted: bool = False


@dataclass
class Candidate:
    candidate_id: str
    name: str


# ----------------------------- Blockchain ----------------------------------
@dataclass
class Block:
    index: int
    timestamp: float
    transactions: list
    previous_hash: str
    nonce: int = 0
    hash: str = field(default="")

    def compute_hash(self) -> str:
        payload = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "transactions": self.transactions,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def mine(self, difficulty: int = DIFFICULTY) -> None:
        prefix = "0" * difficulty
        self.hash = self.compute_hash()
        while not self.hash.startswith(prefix):
            self.nonce += 1
            self.hash = self.compute_hash()


class Blockchain:
    def __init__(self):
        self.chain: list[Block] = []
        genesis = Block(0, time.time(), [{"type": "GENESIS"}], "0" * 64)
        genesis.mine()
        self.chain.append(genesis)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, tx: dict) -> Block:
        """Put one transaction in its own block, mine it, and append it."""
        block = Block(len(self.chain), time.time(), [tx], self.last_block.hash)
        block.mine()
        self.chain.append(block)
        return block

    def is_valid(self) -> tuple[bool, str]:
        prefix = "0" * DIFFICULTY
        for i, block in enumerate(self.chain):
            if block.hash != block.compute_hash():
                return False, f"Block {i}: stored hash does not match contents."
            if not block.hash.startswith(prefix):
                return False, f"Block {i}: hash does not meet difficulty."
            if i > 0 and block.previous_hash != self.chain[i - 1].hash:
                return False, f"Block {i}: previous_hash does not match block {i - 1}."
        return True, "Chain is valid."


# ----------------------------- Election ------------------------------------
class Election:
    def __init__(self):
        self.blockchain = Blockchain()
        self.voters: dict[str, Voter] = {}
        self.candidates: dict[str, Candidate] = {}

    def add_candidate(self, candidate_id: str, name: str) -> str:
        if not candidate_id or not name:
            return "ERROR: candidate ID and name cannot be empty."
        if candidate_id in self.candidates:
            return f"ERROR: candidate ID '{candidate_id}' already exists."
        self.candidates[candidate_id] = Candidate(candidate_id, name)
        self.blockchain.add_transaction(
            {"type": "ADD_CANDIDATE", "candidate_id": candidate_id, "name": name}
        )
        return f"Candidate '{name}' added."

    def add_voter(self, voter_id: str, name: str) -> str:
        if not voter_id or not name:
            return "ERROR: voter ID and name cannot be empty."
        if voter_id in self.voters:
            return f"ERROR: voter ID '{voter_id}' already exists."
        self.voters[voter_id] = Voter(voter_id, name)
        self.blockchain.add_transaction(
            {"type": "ADD_VOTER", "voter_id": voter_id, "name": name}
        )
        return f"Voter '{name}' added."

    def cast_vote(self, voter_id: str, candidate_id: str) -> str:
        voter = self.voters.get(voter_id)
        if voter is None:
            return f"ERROR: voter ID '{voter_id}' not found."
        if voter.has_voted:
            return f"ERROR: voter '{voter.name}' has already voted."
        if candidate_id not in self.candidates:
            return f"ERROR: candidate ID '{candidate_id}' not found."
        voter.has_voted = True
        block = self.blockchain.add_transaction(
            {"type": "VOTE", "voter_id": voter_id, "candidate_id": candidate_id}
        )
        return f"Vote recorded in block #{block.index}."


# ----------------------------- Console UI ----------------------------------
def print_blockchain(blockchain: Blockchain) -> None:
    for block in blockchain.chain:
        print("=" * 70)
        print(f"Block #{block.index}")
        print(f"Timestamp    : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block.timestamp))}")
        print(f"Nonce        : {block.nonce}")
        print(f"Previous Hash: {block.previous_hash}")
        print(f"Hash         : {block.hash}")
        print("Transactions :")
        for tx in block.transactions:
            print(f"   - {json.dumps(tx)}")
    print("=" * 70)


def prompt(text: str) -> str:
    return input(text).strip()


def show_menu() -> None:
    print("\n===== Blockchain Voting System =====")
    print("1. Add Candidate")
    print("2. Add Voter")
    print("3. Cast Vote")
    print("4. Print Blockchain")
    print("5. Validate Chain")
    print("6. Exit")


def main() -> None:
    election = Election()
    while True:
        show_menu()
        try:
            choice = prompt("Choose an option (1-6): ")

            if choice == "1":
                cid = prompt("Candidate ID: ")
                name = prompt("Candidate name: ")
                print(election.add_candidate(cid, name))

            elif choice == "2":
                vid = prompt("Voter ID: ")
                name = prompt("Voter name: ")
                print(election.add_voter(vid, name))

            elif choice == "3":
                if not election.candidates:
                    print("ERROR: no candidates yet. Add a candidate first.")
                    continue
                print("Candidates:")
                for c in election.candidates.values():
                    print(f"  {c.candidate_id}: {c.name}")
                vid = prompt("Voter ID: ")
                cid = prompt("Candidate ID to vote for: ")
                print(election.cast_vote(vid, cid))

            elif choice == "4":
                print_blockchain(election.blockchain)

            elif choice == "5":
                ok, msg = election.blockchain.is_valid()
                print(("VALID: " if ok else "INVALID: ") + msg)

            elif choice == "6":
                print("Goodbye!")
                break

            else:
                print("Invalid choice. Please enter a number from 1 to 6.")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
