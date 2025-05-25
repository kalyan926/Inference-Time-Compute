import streamlit as st
from groq import Groq
import os
import json
from display import html_code

#creating a solution tree
if 'tree' not in st.session_state:
    st.session_state["tree"] = ""

if "search" not in st.session_state:
    st.session_state["method"]="BFS"

with st.sidebar:
    st.session_state["method"]=st.selectbox("Search Method",["BFS","DFS"])


# rendering the coloured node tree in streamlit using htmlcode
def render_tree(tree_json):

    html=html_code(tree_json)

    st.components.v1.html(html,width=1000, height=600,scrolling=True)
    
# tree functions partial solution, add_node_to_tree
def partial_solution(node:dict,path:list,index:int=0,par_sol:list=[]):
        """gives partial solution form root node to child node"""
                    
        par_sol.append(node["value"])
        index=index+1
        if(len(path)==index):
            return par_sol
        return partial_solution(node["children"][path[index]],path,index,par_sol)


def add_node(node:dict,path:list,state:str,value:str,index:int=0):
    index=index+1
    if(len(path)==index):
        p=path.copy()
        p.append(len(node["children"]))
        new_node={
                "state": state,
                "value": value,
                "path": p,
                "children": []  }
        node["children"].append(new_node)

        return node, new_node
    changed_node,leaf_node=add_node(node["children"][path[index]],path,state,value,index)
    node["children"][path[index]]=changed_node
    return node,leaf_node


def add_node_to_tree(path:list,state:str,value:str):

    st.session_state["tree"],leaf_node=add_node(st.session_state["tree"],path,state,value)

    #convert dict to json
    tree_json = json.dumps(st.session_state["tree"])
    render_tree(tree_json)
    return leaf_node

#llm related functions
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def chat(msgs):

    messages=[
            {
                "role": "system",
                "content": "you are reasoning assistant who thinks detailly step by step to reach a solution for a given problem and give only next possible single step completion based on all previous steps for a problem. give only next possible single step per user request until answer is reached."
            } ]    
    messages.extend(msgs)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=1.5,
        max_completion_tokens=2730,
        top_p=1,
        stream=False,
        stop=None )
    
    return response.choices[0].message.content


def parse(input_string):
    # Check for each status in order

    if "NO_PROGRESS" in input_string:
        return "NO_PROGRESS"
    elif "PROGRESS" in input_string:
        return "PROGRESS"
    elif "SOLUTION" in input_string:
        return "SOLUTION"
    else:
        return "None"

def verifier(path:list, response:str):

    """a verifier that verifies whether the next step of partial solution is solution or progress or no progress"""

    par_sol=partial_solution(st.session_state["tree"],path)

    content=""
    first=1
    for i in par_sol:
        if (first==1):
            content="problem:"+"\n"+i+"\n"+"partial solution of the problem:"+"\n"
            first=0
        else:
            content=content+i+"\n"
    content=content+"next step of partial solution:"+"\n"+response
        
    user_message={
                    "role": "user",
                    "content": content
                    }   

    messages=[
        {
            "role": "system",
            "content": """
                            You are an expert verifier of partial solutions. You will be given a problem, a partial solution, and the next step after the partial solution. Your task is to analyze the problem, the partial solution, and determine whether the next step leads to progress or not or solution itself.

                            1.If the next step leads to a solution, respond with PROGRESS.
                            2.If the next step does not lead to a solution, respond with NO_PROGRESS.
                            3.If the next step is the final solution, respond with SOLUTION.

                            Answer in one word based on the above conditions."""}]

    messages.append(user_message)
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=1,
        max_completion_tokens=2730,
        top_p=1,
        stream=False,
        stop=None )
    state=parse(response.choices[0].message.content)
    
    return state

#format messages for llm
def format_messages(node):
    
    par_sol=partial_solution(st.session_state["tree"],node["path"])

    formated_msgs=[]
    start=1
    for msg in par_sol:

        if(start==1):
            formated_msgs.append({"role":"user","content":msg})
            start=0
        else:
            formated_msgs.append({"role":"assistant","content":msg})
            formated_msgs.append({"role":"user","content":"next step"})

    return formated_msgs

#search methods.....

# recursively adds node to the tree by following the Breadth first search until predifined conditions are met
def bfs_search(level:list,samp:int,sol:int,breadth:int=4)->None:

    if(len(level)==0 or sol==0):
        return
    new_level=[]
    count_steps=0  # controls the breadth of tree 
    # no of samplings per node
    for s in range(samp):
        
        if(count_steps==breadth):
            break
        for node in level:
            if(count_steps==breadth):
                break            
            if(sol==0):
                return
            response=chat(format_messages(node))                            
            new_node=""
            #llm verifier verifies the paratial solution and gives progess, no progess, solution
            state=verifier(node["path"],response)
            if state=="PROGRESS":
                new_node=add_node_to_tree(node["path"],"step",response) #adds node to the tree
                new_level.append(new_node)
                count_steps=count_steps+1

            elif state=="NO_PROGRESS":                 
                new_node=add_node_to_tree(node["path"],"terminate",response) #adds node to the tree
            
            elif state=="SOLUTION":                
                new_node=add_node_to_tree(node["path"],"solution",response) #adds node to the tree
                sol=sol-1
                
    bfs_search(new_level,samp,sol,breadth)
    
    return

# recursively adds node to the tree by following the Depth first search until predifined conditions are met
def dfs_search(node:dict,samp:int,sol:int,depth:int=10):

    if depth==0:   
        return
    
    for s in range(samp):
        response=chat(format_messages(node))                            
        new_node=""
        #llm verifier verifies the paratial solution and gives progess, no progess, solution
        state=verifier(node["path"],response)        
        
        if state=="PROGRESS":
            new_node=add_node_to_tree(node["path"],"step",response)#adds node to the tree
            try_again=dfs_search(new_node,samp,sol,depth-1)
            if(try_again=="solution"):
                return "solution"
        if state=="NO_PROGRESS":
            new_node=add_node_to_tree(node["path"],"terminate",response)#adds node to the tree

        if state=="SOLUTION":
            new_node=add_node_to_tree(node["path"],"solution",response)#adds node to the tree
            sol=sol-1
            if(sol==0):
                return "solution"

    return
    

if prompt := st.chat_input("How Can I Help?"):

    if st.session_state["tree"]=="":
        st.session_state["tree"]={
        "state": "problem",
        "value": prompt,
        "path": [0],
        "children": []  }


    if st.session_state["method"]=="BFS":
        bfs_search([st.session_state["tree"]],2,3)

    elif st.session_state["method"]=="DFS":
        dfs_search(st.session_state["tree"],3,3)

    