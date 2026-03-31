#!/bin/bash
COUNT=30
PARALLEL=8  # number of simultaneous processes

seq 1 $COUNT | xargs -n1 -P$PARALLEL -I{} \
python -c "from processors.generation import generate_patient_case; generate_patient_case()"
