pie_chart_config='''1. **tooltip**: 
        - Specify the trigger as 'item'.
    
    2. **legend**: 
        - Position the legend at the top and center.
    
    3. **series**:
        - Provide an array containing the series objects.
        - Each series object should specify:
          - The `name` of the chart.
          - The `type` as 'pie'.
          - The `radius` (e.g., inner and outer radius for a donut chart).
          - An array of `data` objects, each containing `value` and `name` fields.
          - Additional settings like `itemStyle` (e.g., border radius) and `label` for displaying names and percentages.

    For example, the output should look like this:

    {{
      "tooltip": {{
        "trigger": "item"
      }},
      "legend": {{
        "top": "5%",
        "left": "center"
      }},
      "series": [
        {{
          "name": "Access From",
          "type": "pie",
          "radius": ["40%", "70%"],
          "itemStyle": {{
            "borderRadius": 10
          }},
          "data": [
            {{ "value": 1048, "name": "Search Engine" }},
            {{ "value": 735, "name": "Direct" }},
            {{ "value": 580, "name": "Email" }},
            {{ "value": 484, "name": "Union Ads" }},
            {{ "value": 300, "name": "Video Ads" }}
          ],
          "label": {{
            "show": true
          }}
        }}
      ]
    }}

    **Please provide the output as pure, unformatted JSON (without escape characters or any other additional formatting), directly usable in ECharts.** Do not include any extra explanations or markdown.'''

bar_chart_config='''
1. **xAxis**: 
        - Specify if the axis type is 'category' or 'value'.
        - Provide the data to be plotted on the X-axis.
    
    2. **yAxis**: 
        - Specify if the axis type is 'category' or 'value'.
    
    3. **series**:
        - Provide an array of series objects, each containing the data to be plotted on the Y-axis and specifying the type of chart (e.g., 'bar', 'line', 'scatter', etc.).

    For example, the output should look like this:

    {{
      "xAxis": {{
        "type": "category",
        "data": ["Data1", "Data2", ...]
      }},
      "yAxis": {{
        "type": "value"
      }},
      "series": [
        {{
          "data": [120, 200, 150, 80, 70, 110, 130],
          "type": "bar"
        }}
      ]
    }}

    **Please provide the output as pure, unformatted JSON (without escape characters or any other additional formatting), directly usable in ECharts.** Do not include any extra explanations or markdown.
'''
line_graph_config='''
1. **xAxis**: 
        - Specify the axis type (e.g., 'category').
        - Indicate whether `boundaryGap` should be enabled or disabled.
        - Provide the data to be plotted on the X-axis.

    2. **yAxis**: 
        - Specify the axis type (e.g., 'value').
        - Indicate if `boundaryGap` should be applied, and if so, the range values.

    3. **visualMap**:
        - Define the `type` (e.g., 'piecewise').
        - Provide configurations for `dimension`, `seriesIndex`, and an array of `pieces` where each piece defines the range and associated styles (e.g., color).

    4. **series**:
        - Specify the type as 'line'.
        - Provide the `data` to be plotted, with X and Y values.
        - Include settings for `smoothness`, `symbol`, and `lineStyle` (e.g., color, width).
        - Configure `markLine` for marking specific X-axis points and `areaStyle` for shading below the line.

    For example, the output should look like this:

    {{
      "xAxis": {{
        "type": "category",
        "boundaryGap": false
      }},
      "yAxis": {{
        "type": "value",
        "boundaryGap": [0, "30%"]
      }},
      "visualMap": {{
        "type": "piecewise",
        "show": false,
        "dimension": 0,
        "seriesIndex": 0,
        "pieces": [
          {{
            "gt": 1,
            "lt": 3,
            "color": "rgba(0, 0, 180, 0.4)"
          }},
          {{
            "gt": 5,
            "lt": 7,
            "color": "rgba(0, 0, 180, 0.4)"
          }}
        ]
      }},
      "series": [
        {{
          "type": "line",
          "smooth": 0.6,
          "symbol": "none",
          "lineStyle": {{
            "color": "#5470C6",
            "width": 5
          }},
          "markLine": {{
            "symbol": ["none", "none"],
            "label": {{ "show": false }},
            "data": [{{ "xAxis": 1 }}, {{ "xAxis": 3 }}, {{ "xAxis": 5 }}, {{ "xAxis": 7 }}]
          }},
          "areaStyle": {{}},
          "data": [
            ["2019-10-10", 200],
            ["2019-10-11", 560],
            ["2019-10-12", 750],
            ["2019-10-13", 580],
            ["2019-10-14", 250],
            ["2019-10-15", 300],
            ["2019-10-16", 450],
            ["2019-10-17", 300],
            ["2019-10-18", 100]
          ]
        }}
      ]
    }}

    **Please provide the output as pure, unformatted JSON (without escape characters or any other additional formatting), directly usable in ECharts.** Do not include any extra explanations or markdown.
'''