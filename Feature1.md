In this project where we have two main files 
1. [gemini_processor.py](gemini_processor.py)
2. [streamlit_app.py](streamlit_app.py)

We need to update calcualtion done by HERE API
Currently what we are doing is reading data from image using Gemini API and then getting output as JSON this output could have these values 
```
{
    "trip_started_from": "origin city name and state abbreviation with comma (e.g., Bloomington, CA)",
    "first_drop": "first drop city name and state abbreviation with comma (e.g., San Bernardino, CA)",
    "second_drop": "second drop city name and state abbreviation with comma (e.g., San Bernardino, CA)", 
    "third_drop": "third drop city name and state abbreviation with comma - OPTIONAL, leave empty if not clearly visible",
    "forth_drop": "fourth drop city name and state abbreviation with comma - OPTIONAL, leave empty if not clearly visible",
    "inbound_pu": "inbound pickup city name and state abbreviation with comma (e.g., San Bernardino, CA)",
    "drop_off": "final drop off - can be string or array if multiple values separated by 'to'",
}

using these we are using here api to calcualte total miles covered as well as miles covered in each state. But we are only considering those states that are mentioned in values of above json structure and ignore those states from which the truck is actually passed through, For Example:
for this route : `CEDAR RAVINE, CA » MARSHALL, TX » DALLAS, TX » FORNEY, TX » TEMECULA, CA » SAN BERNARDINO, CA`
our outpur is displaying miles of CA and TX only but in actual the truck has coverd some distance in Nivada, Arizona and New Mexico and we didnt calculated that distance. Hence wrong results.
So we need to find a way to draw route on a map and see how many stated are part of the route and them calculate the distance convered in each state. or any othe approach to get distance covered in each state.
