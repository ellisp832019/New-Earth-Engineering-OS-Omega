# Bug Fix Summary

Observed on 2026-08-07.

## Problem

The packaged Windows startup path was too dependent on ephemeral backend port discovery.

## Fix

The desktop now starts the backend on the configured service port and uses bounded health polling against that exact port.

It also fails fast when the backend exits before becoming healthy.

## Supporting changes

- backend startup failure is surfaced in the startup snapshot
- packaged backend and package smoke harness scripts were added
- release evidence now records the diagnosis and the intended process topology
