#!/bin/bash

# Log file
log_file="/home/lmex89/Documentos/logs/folder_cleaning_log.txt"

# Log the date and time of the operation
echo "Folder cleaning started at $(date)" >> "$log_file"

# Directory to be cleaned
directory_to_clean="/media/lmex89/backup/Plex/downloads/completed"

# Check if the directory exists before deleting its contents
if [ -d "$directory_to_clean" ]; then
    # List all the files to be deleted 
    echo "Files to be deleted:" >> "$log_file"
    ls -la "$directory_to_clean" >> "$log_file"

    # Remove all files and subdirectories within the specified directory
    rm -rf "${directory_to_clean}"/*

    # Log the operation completion
    echo "Folder content deleted at $(date)" >> "$log_file"
else
    echo "Directory not found or inaccessible" >> "$log_file"
fi

