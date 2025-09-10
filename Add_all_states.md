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



## update
Current when I run my program on below images I am getting [this](test/output/actual_resutls.csv) result

![Image 1](test/images/1.jpg)
![Image 2](test/images/2.jpg)
![Image 3](test/images/3.jpg)
![Image 4](test/images/4.jpg)
![Image 5](test/images/5.jpg)
![Image 6](test/images/6.jpg)
![Image 7](test/images/7.jpg)
![Image 8](test/images/8.jpg)
![Image 9](test/images/9.jpg)

But the expected result should be [this](test/output/expected_output.csv)

so there are two issues one is formatting which we wil deal with later but actual issue is the states missmatch.
we can see total number of stated in actual output is far more than that in expected_output.csv 


### some issues 
test/output/actual_resutls.csv has these states
AR	3446
AZ	3273
CA	3221
IA	3306
IL	3468
IN	1879
KY	2151
MO	2194
NC	1785
NE	2149
NM	2016
NV	1751
OK	1715
TN	1774
TX	2045
UT	2089
VA	1680
WY	2048



test/output/expected_output.csv has these states
AR	1423
AZ	6963
CA	3565
IL	1411
IN	872
MO	2632
NM	6719
OK	5206
TN	1623
TX	7025
KY	98
NC	487


each envelop data
test/output/actual_resutls.csv has these states
1	4136.4
2	4721.9
3	4312.2
4	4055.2
5	8110.4
6	4847.3
7	3657
8	5541.2
9	3370.8


test/output/expected_output.csv has these states
1	4146
2	4160
3	4192
4	4081
5	4111
6	6277
7	4013
8	3782
9	3262

% difference in envelop
1	0%
2	14%
3	4%
4	-2%
5	96%
6	17%
7	-12%
8	34%
9	-19%

