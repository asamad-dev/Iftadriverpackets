# Editable Result Dashboard in Streamlit App
we have a result dashboard in our streamlit application, where first of all we are getting some values from Gemini API and pasting them as it is. and then we have some values that are calcualted from HERE API.
We need an updated result dashboard on will be editable for all values that are extarcted by Gemini. The main purpose of this is to correct values that are extracted by Gemini API from an image. There is always a cahnce tha Gemini will give us few wrong values.

## Part 1: 
Result dashboard mush show all values that are mentioed in return JSON format of LLM, mentioned in Prompt (see self.extraction_prompt in [gemini_processor.py](gemini_processor.py))
Right now we are only displaying those which have value, but we should display all of them because there is a chance Gemini miss a value and its field will now displayed in result dashboard.
hance we need all fields.

## Part 2:
We should have now a calcualte button which will be enable when we change any Gemini Extracted value, and when calcualte is pressed then it will run HERE API related code again and display updated results. 

## Implementation details.
We will make it as simple as we can but We are allowed to refactor code if required to make this feature successfull. for this we have to think like solution architect with decade of Python development experience.