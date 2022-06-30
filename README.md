# Hyper Predictive RV

A Python tool to achieve Hyper Predictive Runtime Verification.

## How to install

- Install https://pm4py.fit.fraunhofer.de/

## How to use

To run the tool

```bash
-$ python main.py <path_to_XES_file> <number_of_threads>
```

where:
- <path_to_XES_file> is the path to the XES file containing the event logs of previous system executions
- <number_of_threads> is the number of threads to consider in the verification of the Petri Net

## Try an example

To run the tool on an example

```bash
-$ python3 main.py ./lock1.xes 2
```

The tool should print ERROR (we have concurrent access on the same shared variable). 
