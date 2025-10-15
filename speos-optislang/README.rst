Speos, optiSLang workflow
=========================

Below is an example workflow that demonstrates how to perform an optical lightguide robustness
study, set up the robustness workflow, and run an optical simulation using PyAnsys. The lightguide
is prepared in Speos and exported as a .speos file. The exported file is processed by pySpeos to
run a parametric study, controlled by PyOptiSLang, in order to evaluate the to understand the
influence of source power, source position on the lightguide performance, i.e. RMS contrast,
average luminance as well as the number of failed regulations
