# HOW TO GIT

## Intro

In this section I want to set some guide lines on how to use git and what commands we need.

## Git Structure

we have 2 main branches:

+ main
+ dev

we do development related stuff in dev branch and whenever its ready for production it will tagged with a version and merged with main branch (the production branch)

## Git Features and Bugfix Branches

in the process of developing we mainly do two things :
    1. adding new features
    2. fixing bugs

so we have two kind of branches that come from dev branch :
    1. feature/[name-of-feature]
    2. bugfix/[name-of-bug]

any thing that we add to the project we should consider it as feature (from very small change to the code like adding comments or refactoring small section of code up to adding fully working new "Feature").

and any thing that we do to fix bugs will goes under bugfix branch.

Note: these two branch should only come from dev and merge with dev only.

## Git Commands

### 1. Status

```console
$ git status
```

to check what's up in the active repo

### 2. Add Files

``` console
$ git add [file name] # for specific file
$ git add . # for all files in the current directory
$ git add -A # for all files
```

to add file or files to the stage section

### 3. Commit

``` console
$ git commit -m 'commit msg'
```

to commit change

### 4. Log

``` console
$ git log
```

to see all the commits

### 5. Branches

``` console
$ git branch -r
```

to see all active branches

### 6. Create Branch

``` console
$ git branch [branch name]
```

to create new brach out of the current branch


### 7. Publish Branch

``` console
$ git push --set-upstream origin new-branch
```
use this command to push new branch to remote repo.

### 8. Checkout

``` console
$ git checkout [branch_name]
```

to change current working branch to the given branch

### 9. Merge

``` console
$ git merge [branch_name]

```

to merge given branch with current branch

## Work Flow

our work flow in this project should be something like this :

let say we have to add Oauth2 system with google

first we make sure that we are in the dev branch '`git checkout dev`'

then we pull dev to have newest code '`git pull origin dev`'

then create new branch name 'feature/Oath2-google' '`git branch feature/Oath2-google`'

then we publish the new branch to remote repo '`git push --set-upstream origin feature/Oath2-google`'

then we move to new branch '`git checkout feature/Oath2-google`'

then we make sure that we are in the new branch '`git status`'

after that we do some coding and make some commits '`git add .`' and '`git commit -m 'msg'`'

and always push the code '`git push origin feature/Oath2-google`'

then we should wait for code review meet and hopefully everything is right.

## Git Policies

1.  First of all we should always use discussed branch tree.

2.  Use this [link](https://www.conventionalcommits.org/en/v1.0.0/) as manifesto of git commit messages this will be painfull but will worth it.