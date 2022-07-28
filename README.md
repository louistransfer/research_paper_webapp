# Introduction

This project was built to present the results of my Research Paper on the use of data science techniques in the Venture Capital industry. The document as well as additional plots can be downloaded from the platform.

The code presented here is used to run my webapp available here : [https://louistransfer-research-paper-analysis-home-co337u.streamlitapp.com/](https://louistransfer-research-paper-analysis-home-co337u.streamlitapp.com/).

# Good practices

The code follows code and DevOps good practices :

- The code is run through black to format it;
- The files are organized in a central "analyzer" module, containing helper files with functions which are typed;
- Every function is typed in order to have consistency on the input and output;
- Secrets are contained in a toml file. This repo contains a sample toml with the informations I provide to the app;
- Config variables are contained in a config.toml file which is loaded into streamlit session state. This way, every page of the webapp can access the variables;
- Due to streamlit cloud constraints, I can only use a requirements.txt file instead of a Poetry structure to handle packages.

Functions still need a docstring though, and tests could be added, in particular on the importation phase.

# Architecture

![Webapp architecture](assets/images/webapp_architecture.png)

The webapp front is generated by streamlit. The analyser files contain ingestion scripts which retrieve data from 2 sources : Google Forms and Google Sheets. The data is then automatically processed to generate the necessary datasets. Plots are generated with the Plotly package and can be exported as png files.

The data is exportable in .xlsx and .csv formats. That way the results of the analysis can be replicated.

**Note**: I developed the app on a private repo, where I ran my merge requests. I decided not to make it public as some notebooks I used during development could leak sensitive information. Therefore, this code is merely for presentation purpose, as the webapp runs on my private repo where all development is made.