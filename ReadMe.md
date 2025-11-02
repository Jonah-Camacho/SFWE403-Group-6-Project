# This program requires Node to be installed.

A bash script is included in the files.
It is good practice to read the script before executing.
The script will install install dependencies when needed, otherwise it will start the server. 

## To install and/or run the server using the script:
```
./start.sh
```
## If you prefer to not use the script
### Installation: 
```
npm install
```
### Run the Server:
```
npm run dev
```

# This program will also require ollama to be installed with an llm model.

## Open a terminal (Powershell or Command prompt)

## Install Ollama via Winget
```
winget install Ollama.Ollama --silent --accept-source-agreements --accept-package-agreements
```

## Restart your terminal and verify
```
ollama --version
```

## Now download the model that you will be using
```
ollama pull [model name]
```
- example would be:
  ```
  ollama pull llama3.1
  ```

## Verify model is installed
```
ollama list
```
- The models downloaded should be shown
- make sure to edit the python file to use the model downloaded.
