#run polyply create system minimise then extend the box and stabilise before running nvt


#!/bin/bash
source /usr/local/gromacs/bin/GMXRC

BASE=/home/location

#selecting on specific concentrations to speed up the process.

for folder in blend_10 blend_30 blend_50 blend_70 blend_90; do

    cd $BASE/$folder || exit

    # build starting system
    polyply gen_coords -p system.top -o starting_blend.gro -name P3HT_PS_blend -dens 1000

    # extend box to 50 nm in z
    coord=$(tail -n 1 starting_blend.gro)
    declare -a colArray=($(echo $coord | tr ',' ' '))

    colArray[2]=50.00

    gmx editconf \
        -f starting_blend.gro \
        -box "${colArray[@]}" \
        -c \
        -o extended.gro

    # minimise
    gmx grompp -f min.mdp \
        -c extended.gro \
        -p system.top \
        -o min.tpr \
        -maxwarn 5

    gmx mdrun \
        -deffnm min \
        -nb gpu \
        -ntmpi 1 \
        -ntomp 12 \
        -v


    # stabilise
    gmx grompp -f stable.mdp \
        -c min.gro \
        -p system.top \
        -o stable.tpr \
        -maxwarn 5

    gmx mdrun \
        -deffnm stable \
        -nb gpu \
        -ntmpi 1 \
        -ntomp 12 \
        -v

    #production
    gmx grompp -f npt.mdp \
        -c stable.gro \
        -t stable.cpt \
        -p system.top \
        -o NPT.tpr \
        -maxwarn 5

    gmx mdrun \
        -deffnm NPT \
        -nb gpu \
        -bonded gpu \
        -update gpu \
        -ntmpi 1 \
        -ntomp 12 \
        -pin on \
        -v


done
