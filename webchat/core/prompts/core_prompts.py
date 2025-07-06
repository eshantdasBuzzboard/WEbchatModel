from langchain_core.prompts import ChatPromptTemplate


website_updatte_content_system_prompt = """
You are an excellent agent in updating website content based on query or request. You will be given 
a lot of information like website content. You will also be given a left panel information about 
the specific page of the website content. If it has a key value pair of key as content and the information 
is available like not null make sure you use that precisely. If it has keywords then do not miss that.
This is about the left panel information.

You need to highly focus on the query requested by the user and based on that you need to update the 
current website page output. So you will also be given the current website output and based on that you need to update it
in whatever the user is requesting in his or her query and you need to update it accordingly pretty well.
Just update the section or sections they are mentioning about and return the other key value of the output as it is.
Make sure you return the output in the same json structure in which you are being given in the input and there is no change there.
So now all you need to do is highly focus on the query which the user sends and generate or update or remove or add
the section of the website content which the user is asking considering the "business information" and the "left panel information".
You need to just keep those info in your mind and based on that you need to generate . Highly focus on the content section of the left panel information if it is not null.
"""


website_update_content_user_prompt = """
Here is your business info 
<business_info>
{business_info}
</business_info>

Here is your left panel info
<left_panel_info>
{left_panel_info}
<left_panel_info>

Here is the output of the website page which you need to update and return in the same json structure 
as it is
<current_output>
{current_output}
</current_output>

Here is the main query which you need to focus on and based on that update the specific section of the  current output
<query>
{query}
</query>

Make sure you return in the same structure as the current output.
"""

website_update_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", website_updatte_content_system_prompt),
        ("human", website_update_content_user_prompt),
    ]
)
