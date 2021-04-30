# Active control of the flow past a cylinder at varying Reynolds number

This research project is a direct continuation of the work by [Darshan Thummar](https://github.com/darshan315/flow_past_cylinder_by_DRL). The repository is structured as follows:
- *test_cases*: OpenFOAM simulation setups

## Getting started

To run a test case, create a *run* folder (ignored by version control), copy the case from *test_cases* to *run*, and execute the *Allrun* script. To run with Singularity, the image has to be built fist; see *Singularity and SLURM*.

```
mkdir -p run
cp -r test_cases/cylinder2D_base run/
cd run/cylinder2D_base
# for execution with singularity
./Allrun.singularity
# for execution for local OpenFOAM installation
./Allrun
```

## Singularity and SLURM

[Singularity]() is a container tool that allows making results reproducible and performing simulations, to a large extent, platform independent. The only remaining dependencies are Singularity itself and Open-MPI (see next section for further comments). To build the image, run:

```
sudo singularity build of_v2012.sif docker://andreweiner/of_pytorch:of2012-py1.7.1-cpu
```
To run a simulation with Singularity, use the dedicated *Allrun.singularity* scripts. TU Braunschweig's HPC uses the SLURM scheduler. The repository contains an annotated example *jobscript*. The script expects the Singularity image in the top level directory of this repository and the simulation folder in *run*. To submit a job, run:

```
sbatch jobscript name_of_simulation
```
To show all running jobs of a user, use `squeue -u $USER`. Another helpful command is `quota -s` to check the available disk space.