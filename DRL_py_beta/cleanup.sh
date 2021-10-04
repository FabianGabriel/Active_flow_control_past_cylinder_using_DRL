#!/bin/bash -l        
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --time=00:10:00
#SBATCH --job-name=cleanup
#SBATCH --ntasks-per-node=1

rm -rf ./failed
rm -rf ./Data
rm -rf ./results
rm -rf slurm*
rm -rf env/sample_*
rm -rf __pycache__
rm -rf py.log
rm -rf ./env/base_case/agentRotatingWallVelocity/policy.pt

cp ./agentRotatingWallVelocity/test/policy.pt ./env/base_case/agentRotatingWallVelocity/policy.pt