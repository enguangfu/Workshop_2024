#!/bin/bash

# set the location of the btree_chromo files
btree_chromo_files='/projects/bbsv/brg4/btree_chromo_files'

# set the main directory for the project/workshop and the user's subdirectory
project_dir='/projects/bbsv'
user_subdir=${project_dir}/${USER}

# create a workspace for btree_chromo
workspace_dir=${user_subdir}/btree_chromo_workspace
mkdir ${workspace_dir}

# copy the example files
cp -r ${btree_chromo_files}/examples ${workspace_dir}/examples




