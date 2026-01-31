# Firestation Mapper
A simple command line tool to generate a map of firestations in a given area using OpenStreetMap data.

## Usage
For the best results use the `main.py` script. The `main_num.py` script is older and less efficient.

### Arguments
- `-l` or `--location`: The location to search for firestations (e.g., "New York, NY").
- `-t` or `--time`: The maximum travel time in minutes to reach firestations (default is 6 minutes).
- `-o` or `--output`: The output file name for the generated map (e.g., "firestations_map.html"). A default name will be generated based on the location if not provided.
- `-s` or `--speed-increase`: The amount the emergency vehicle is allowed to surpass the speed limit (default is 20).

### Example Command
```bash
python main.py -l "San Francisco, CA" -t 8 -o "sf_firestations_map.html" -s 25
```

### Requirements
- Python 3.x
- Required Python packages can be installed via pip:
```bash
pip install -r requirements.txt
```
### Notes
- Ensure you have an active internet connection as the tool fetches data from OpenStreetMap.
- The generated map will be saved as an HTML file which can be opened in any web browser
- Adjust the speed increase parameter based on local traffic laws and conditions for more accurate results.
- For large locations, the processing time may be longer due to the volume of data being handled.
