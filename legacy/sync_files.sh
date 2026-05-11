#!/bin/bash

# Source and destination folders
source_folder="/mnt/data/Plex/downloads/completed"
destination_folder="/mnt/data/Plex/movies"

# Synchronize files using rsync, without deleting any in the destination
timestamp=$(date +"%Y-%m-%d %T")

# Logging the start of the synchronization process
echo "========== Sync Started: $timestamp =========="
rsync -av --ignore-existing "$source_folder/" "$destination_folder/"

timestamp=$(date +"%Y-%m-%d %T")
echo "========== Sync Completed: $timestamp =========="

