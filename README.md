# Hyper Predictive RV

A Python tool to achieve Hyper Predictive Runtime Verification.

## How to install

- Install https://pm4py.fit.fraunhofer.de/

## How to use

To run the tool

```bash
-$ python main.py <path_to_XES_files> <thread_multiplier>
```

where:
- <path_to_XES_files> is the path to the XES files containing the event logs of previous system executions; each log file denotes multiple executions of the same thread.
- <thread_multiplier> is the multiplier for the number of threads to consider in the verification of the Petri Net (1 means same number of threads as in log files, 2 double number of threads, and so on)

## Try an example

To run the tool on an example

```bash
-$ python3 main.py lock1.xes,lock2.xes 1
```

The tool should print ERROR (we have concurrent access on the same shared variable).
