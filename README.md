# Lazy Deploy

## Description

This project provides rudimentary source tracking for metadata deployment to scratch orgs.

## Overview

Lazy Deploy leverages git source control and the last modified time of files to determine which changes are not present on your org. These files are copied to a temporary directory and deployed together, to ensure all dependencies are met. For best results, initialize Lazy Deploy immediately following an org spin.

## Usage

Initialize if needed, otherwise deploy changes.
```
lazy
```
Reset cache, useful after spinning an org that is already tracked.
```
lazy -r
```

## Installation
```
python3 -m pip install --upgrade git+https://github.com/rolflocherncino/LazyDeploy
```

## Contact

Slack: @rolf.locher

Email: rolf.locher@ncino.com
