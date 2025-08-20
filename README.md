# TimelineTools

Python scripts for managing a collection of files with a predetermined structure.

## Non Refined Drafts

These scripts are currently drafts and may not work as intended.

## Usage and CC0 License

These files are for adapting to other use cases - not for using as-is.
CC0 license means you can use it how you want without conditions.
Giving credit is not required but you can if you want.

## Timeline Custom File Structure

These Tools are designed for a Timeline Collection with a predetermined file structure.
  - A Timeline is a collection of files that are ordered by datetime
  - all filenames begin with a datetime
  - All collection files are within top level folders
  - Top level folders contain no subfolders. Its quite flat.

The root of the collection is the root of a drive or volume. for example, an sdcard, D:\
  - Files in the root of the drive are excluded from the collection.
  - All collection files are within top level folders.

**Some** folders directly in the collection root are excluded from the collection
  - folders beginning with an underscore "_" and some system folders
  - all other folders are considered part of the collection.


## Script Strategy

Target collections on sdcards.
- There is some accommodation for working safely with removable flash memory.
Intended to be simple.
- Not a black box solution.
- No expectation of trust.
- readable and understandable by an individual.
