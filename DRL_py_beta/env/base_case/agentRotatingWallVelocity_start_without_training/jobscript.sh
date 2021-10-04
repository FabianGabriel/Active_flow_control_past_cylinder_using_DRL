#!/bin/bash -l        
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --time=08:00:00
#SBATCH --job-name=no_train
#SBATCH --ntasks-per-node=4

module load singularity/3.6.0rc2
module load mpi/openmpi/4.0.1/cuda_aware_gcc_6.3.0

cd ./env/run/sample_*/

./Allrun.singularity

touch finished.txt