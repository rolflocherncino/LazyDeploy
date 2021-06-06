# Lazy Deploy

## Description

This project provides rudimentary source tracking for metadata deployment to scratch orgs.

## Overview

Lazy Deploy logs the commit of the last successful deployment to diff against the latest commit. Untracked files are added to this list. The last modified time of these files are stored to ensure that only dirty files are deployed between commits. These files are copied to a temporary directory and deployed together, to ensure all dependencies are met. For best results, initialize Lazy Deploy immediately following an org spin.

## Usage

Initialize if needed, otherwise deploy changes.
```
lazy
```
Reset cache, useful after spinning an org that is already tracked.
```
lazy -r
```

## Contact

Slack: @rolf.locher

Email: rolf.locher@ncino.com