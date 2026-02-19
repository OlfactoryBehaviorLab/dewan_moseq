from pathlib import Path
from dewan_moseq import readh5
PATH = "../test_data/results.h5"
print(Path.cwd())
def main():
    readh5.readh5(Path(PATH))


if __name__ == "__main__":
    main()