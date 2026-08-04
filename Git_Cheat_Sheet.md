# Git Commands Cheat Sheet (Production-Oriented)

## Repository Setup

  ----------------------------------------------------------------------------------------
  Command                                              What it does
  ---------------------------------------------------- -----------------------------------
  `git init`                                           Initialize a new Git repository.

  `git clone <url>`                                    Clone an existing repository.

  `git config --global user.name "Name"`               Set your Git username.

  `git config --global user.email "you@example.com"`   Set your Git email.

  `git config --list`                                  View Git configuration.
  ----------------------------------------------------------------------------------------

------------------------------------------------------------------------

# Repository Status

  Command                       What it does
  ----------------------------- ---------------------------
  `git status`                  Show working tree status.
  `git status -s`               Short status output.
  `git diff`                    Show unstaged changes.
  `git diff --staged`           Show staged changes.
  `git diff branch1..branch2`   Compare two branches.

------------------------------------------------------------------------

# Staging

  Command                           What it does
  --------------------------------- ----------------------------------------
  `git add file.cpp`                Stage one file.
  `git add .`                       Stage all new/modified files.
  `git add -A`                      Stage all changes including deletions.
  `git restore --staged file.cpp`   Unstage a file.

------------------------------------------------------------------------

# Commits

  -----------------------------------------------------------------------
  Command                             What it does
  ----------------------------------- -----------------------------------
  `git commit -m "message"`           Create a commit.

  `git commit -am "message"`          Stage tracked files and commit.

  `git commit --amend`                Modify the last commit.

  `git commit --amend --no-edit`      Add staged changes to previous
                                      commit.
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# Branches

  Command                    What it does
  -------------------------- ------------------------
  `git branch`               List local branches.
  `git branch -a`            List all branches.
  `git branch feature`       Create branch.
  `git switch feature`       Switch branch.
  `git switch -c feature`    Create and switch.
  `git checkout feature`     Older switch command.
  `git branch -m new-name`   Rename current branch.
  `git branch -m old new`    Rename another branch.
  `git branch -d feature`    Delete merged branch.
  `git branch -D feature`    Force delete branch.

------------------------------------------------------------------------

# Remote

  Command                             What it does
  ----------------------------------- --------------------------
  `git remote -v`                     Show remotes.
  `git remote add origin <url>`       Add remote.
  `git fetch`                         Download remote changes.
  `git pull`                          Fetch and merge.
  `git pull --rebase`                 Fetch and rebase.
  `git push`                          Push current branch.
  `git push -u origin branch`         Push and set upstream.
  `git push origin --delete branch`   Delete remote branch.

------------------------------------------------------------------------

# Merge & Rebase

  Command                       What it does
  ----------------------------- ----------------------------------
  `git merge feature`           Merge branch into current.
  `git merge --no-ff feature`   Always create merge commit.
  `git rebase main`             Rebase current branch onto main.
  `git rebase --continue`       Continue rebase.
  `git rebase --abort`          Cancel rebase.

------------------------------------------------------------------------

# Stash

  Command             What it does
  ------------------- ----------------------------------
  `git stash`         Save uncommitted work.
  `git stash list`    List stashes.
  `git stash pop`     Restore and remove latest stash.
  `git stash apply`   Restore without removing.
  `git stash drop`    Delete latest stash.
  `git stash clear`   Remove all stashes.

------------------------------------------------------------------------

# History

  Command                             What it does
  ----------------------------------- -----------------------
  `git log`                           Commit history.
  `git log --oneline --graph --all`   Compact graph view.
  `git show <commit>`                 Show commit details.
  `git blame file.cpp`                Show line authorship.

------------------------------------------------------------------------

# Undo

  Command                      What it does
  ---------------------------- -----------------------------
  `git restore file.cpp`       Discard unstaged changes.
  `git restore .`              Restore all files.
  `git reset HEAD file.cpp`    Unstage file.
  `git reset --soft HEAD~1`    Undo commit, keep staged.
  `git reset --mixed HEAD~1`   Undo commit, keep files.
  `git reset --hard HEAD~1`    Discard commit and changes.
  `git revert <commit>`        Safely reverse a commit.

------------------------------------------------------------------------

# Tags

  Command                  What it does
  ------------------------ ----------------
  `git tag`                List tags.
  `git tag v1.0`           Create tag.
  `git push origin v1.0`   Push tag.
  `git push --tags`        Push all tags.

------------------------------------------------------------------------

# Cleaning

  Command           What it does
  ----------------- ---------------------------------
  `git clean -n`    Preview untracked deletion.
  `git clean -fd`   Delete untracked files/folders.

------------------------------------------------------------------------

# Inspection

  Command                What it does
  ---------------------- --------------------------------
  `git ls-files`         List tracked files.
  `git rev-parse HEAD`   Current commit hash.
  `git reflog`           Recover lost commits/branches.

------------------------------------------------------------------------

# Cherry-pick

  Command                      What it does
  ---------------------------- -------------------------------------
  `git cherry-pick <commit>`   Apply a commit onto current branch.
  `git cherry-pick --abort`    Cancel cherry-pick.

------------------------------------------------------------------------

# Useful Production Aliases

``` bash
git log --oneline --graph --decorate --all
git fetch --all --prune
git pull --rebase
git stash
git rebase main
git cherry-pick <hash>
git revert <hash>
git reflog
```

------------------------------------------------------------------------

# Typical Team Workflow

``` text
git switch main
git pull --rebase

git switch -c feature/login

# Work...
git add .
git commit -m "Add login validation"

git push -u origin feature/login

# Open Pull Request

# After merge
git switch main
git pull
git branch -d feature/login
```

------------------------------------------------------------------------

# Commands Used Most Often by Production Teams

-   `git status`
-   `git add`
-   `git commit`
-   `git switch`
-   `git branch`
-   `git fetch`
-   `git pull --rebase`
-   `git push`
-   `git merge`
-   `git rebase`
-   `git stash`
-   `git log --oneline --graph --all`
-   `git diff`
-   `git restore`
-   `git revert`
-   `git cherry-pick`
-   `git reflog`
-   `git tag`
-   `git remote -v`
