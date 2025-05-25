import json


NODE_COLORS = {
    "problem": "grey",
    "step": "yellow",
    "terminate": "red",
    "solution": "green"
}


def html_code(tree_json):

    HTML_CODE=f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Tree Visualization</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; }}
                canvas {{ border: 0px solid black; margin-top: 10px; }}
                .tooltip {{
                    position: absolute;
                    visibility: hidden;
                    background: white;
                    padding: 5px;
                    border: 1px solid black;
                    border-radius: 3px;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div id="tooltip" class="tooltip"></div>
            <canvas id="treeCanvas" width="900" height="600"></canvas>
            <script>
                let treeData = {tree_json};  // Load tree data from Streamlit
                const canvas = document.getElementById("treeCanvas");
                const ctx = canvas.getContext("2d");
                const tooltip = document.getElementById("tooltip");

                function drawArrow(x1, y1, x2, y2) {{
                    const dx = x2 - x1, dy = y2 - y1;
                    const angle = Math.atan2(dy, dx);
                    ctx.strokeStyle = "black";
                    ctx.setLineDash([5, 5]);
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();
                    
                    // Draw arrowhead
                    ctx.setLineDash([]); 
                    ctx.beginPath();
                    ctx.moveTo(x2, y2);
                    ctx.lineTo(x2 - 10 * Math.cos(angle - Math.PI / 6), y2 - 10 * Math.sin(angle - Math.PI / 6));
                    ctx.lineTo(x2 - 10 * Math.cos(angle + Math.PI / 6), y2 - 10 * Math.sin(angle + Math.PI / 6));
                    ctx.closePath();
                    ctx.fillStyle = "black";
                    ctx.fill();
                }}

                function drawTree(node, x, y, level = 0) {{
                    let colorMap = {json.dumps(NODE_COLORS)};
                    let color = colorMap[node.state] || "grey";
                    
                    ctx.fillStyle = color;
                    ctx.beginPath();
                    ctx.arc(x, y, 20, 0, 2 * Math.PI);
                    ctx.fill();
                    ctx.stroke();

                    ctx.fillStyle = "white";
                    ctx.font = "12px Arial";
                    ctx.textAlign = "center";
                    ctx.fillText("", x, y + 5);

                    const childY = y + 100;
                    const spacing = 250 / (node.children.length + 1);
                    node.children.forEach((child, i) => {{
                        const childX = x + (i - node.children.length / 2) * spacing * (3 - level);
                        drawArrow(x, y + 20, childX, childY - 20);
                        drawTree(child, childX, childY, level + 1);
                    }});

                    return {{ x, y, radius: 20, value: node.value }};
                }}

                function renderTree() {{
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    let nodes = [];
                    function collectNodes(node, x, y, level = 0) {{
                        nodes.push(drawTree(node, x, y, level));
                        const childY = y + 100;
                        const spacing = 250 / (node.children.length + 1);
                        node.children.forEach((child, i) => {{
                            const childX = x + (i - node.children.length / 2) * spacing * (3 - level);
                            collectNodes(child, childX, childY, level + 1);
                        }});
                    }}
                    collectNodes(treeData, canvas.width / 2, 50);

                    canvas.onmousemove = function(event) {{
                        const rect = canvas.getBoundingClientRect();
                        const mouseX = event.clientX - rect.left;
                        const mouseY = event.clientY - rect.top;
                        let found = false;

                        nodes.forEach(node => {{
                            const dx = mouseX - node.x;
                            const dy = mouseY - node.y;
                            if (Math.sqrt(dx * dx + dy * dy) < node.radius) {{
                                tooltip.style.left = (event.pageX + 10) + "px";
                                tooltip.style.top = (event.pageY - 10) + "px";
                                tooltip.innerHTML = node.value;
                                tooltip.style.visibility = "visible";
                                found = true;
                            }}
                        }});

                        if (!found) {{
                            tooltip.style.visibility = "hidden";
                        }}
                    }};
                }}

                renderTree();
            </script>
        </body>
        </html>
        """
    return HTML_CODE