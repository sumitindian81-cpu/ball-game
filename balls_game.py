from typing import List


class Tube:
    def __init__(self, capacity: int, balls: List[str] = None):
        self.capacity = capacity
        self.balls = balls[:] if balls else []

    def is_empty(self) -> bool:
        return len(self.balls) == 0

    def is_full(self) -> bool:
        return len(self.balls) >= self.capacity

    def top(self):
        return self.balls[-1] if self.balls else None

    def can_move_to(self, other: "Tube") -> bool:
        """
        FREE MODE: User koi bhi ball kisi bhi tube me daal sakta hai.
        Sirf 2 rules:
        1. Source tube empty nahi honi chahiye
        2. Destination tube full nahi honi chahiye
        """
        if self.is_empty():
            return False
        if other.is_full():
            return False
        return True

    def pop(self):
        if self.is_empty():
            return None
        return self.balls.pop()

    def push(self, color: str):
        if self.is_full():
            raise ValueError("Tube is full")
        self.balls.append(color)

    def is_uniform_or_empty(self) -> bool:
        """Tube ya to empty ho ya pura ek hi color se bhari ho"""
        if self.is_empty():
            return True
        if len(self.balls) != self.capacity:
            return False
        return len(set(self.balls)) == 1

    def __repr__(self):
        return f"Tube({self.balls})"


class Game:
    def __init__(self, tubes: List[Tube]):
        self.tubes = tubes
        self.moves = 0

    def move(self, src_idx: int, dst_idx: int) -> bool:
        """Try to move one ball from src to dst. Return True if moved."""
        src = self.tubes[src_idx]
        dst = self.tubes[dst_idx]

        if src.can_move_to(dst):
            ball = src.pop()
            dst.push(ball)
            self.moves += 1
            return True
        return False

    def is_completed(self) -> bool:
        """Win condition: har tube ya empty ho ya same color se completely bhari ho"""
        return all(t.is_uniform_or_empty() for t in self.tubes)

    def print_state(self):
        print(f"Moves: {self.moves}")
        h = max(t.capacity for t in self.tubes)
        for level in range(h - 1, -1, -1):
            row = []
            for t in self.tubes:
                if level < len(t.balls):
                    row.append(t.balls[level][0])
                else:
                    row.append(" ")
            print(" | ".join(row))
        print("-" * (4 * len(self.tubes) - 3))
        print("   ".join(str(i) for i in range(len(self.tubes))))
        print()


def create_sample_level() -> Game:
    """Sample level: 3 colors mixed, 2 empty tubes for sorting"""
    capacity = 4
    tubes = [
        Tube(capacity, ["R", "G", "B", "R"]),
        Tube(capacity, ["G", "B", "R", "G"]),
        Tube(capacity, ["B", "R", "G", "B"]),
        Tube(capacity, []),
        Tube(capacity, []),
    ]
    return Game(tubes)


def main():
    """Console version for testing"""
    game = create_sample_level()

    while True:
        game.print_state()
        if game.is_completed():
            print("LEVEL COMPLETE!")
            break

        try:
            raw = input("Move (src dst) e.g. '0 3' or 'q' to quit: ")
            if raw.lower() == "q":
                break
            src, dst = map(int, raw.split())
        except Exception:
            print("Invalid input.")
            continue

        if not (0 <= src < len(game.tubes) and 0 <= dst < len(game.tubes)):
            print("Index out of range.")
            continue

        if not game.move(src, dst):
            print("Move not allowed (source empty or destination full).")


if __name__ == "__main__":
    main()