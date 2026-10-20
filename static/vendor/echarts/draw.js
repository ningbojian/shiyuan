/* ECharts renderers for the shiyuan detail page. */
function drawmap(id, data, min, max, second) {
    var chart = echarts.init(document.getElementById(id));
    chart.setOption({
        title: { text: second + "姓人口分布", left: "center", textStyle: { fontSize: 14 } },
        tooltip: { trigger: "item", formatter: "{b}: {c}" },
        visualMap: {
            min: min, max: max, text: ["高", "低"], realtime: false,
            calculable: true, inRange: { color: ["#e8f1f2", "#f6d365", "#b55239"] }
        },
        series: [{
            type: "map", name: "人口占比", mapType: "china",
            data: data, label: { show: false }, roam: true,
            emphasis: { label: { show: true } }
        }]
    });
}

function drawtree(id, treedata, second) {
    var chart = echarts.init(document.getElementById(id));
    var children = (treedata || []).filter(function (item) {
        return item && (item.value > 0 || (item.children && item.children.length));
    });
    chart.setOption({
        tooltip: { trigger: "item" },
        series: [{
            type: "tree",
            data: [{ name: second + "姓", children: children }],
            top: "4%", left: "8%", bottom: "4%", right: "18%",
            symbolSize: 8, roam: true,
            label: { position: "left", verticalAlign: "middle", align: "right", fontSize: 12 },
            leaves: { label: { position: "right", align: "left" } },
            expandAndCollapse: true,
            animationDuration: 400
        }]
    });
}

function drawwordcloud(id, data, second) {
    var chart = echarts.init(document.getElementById(id));
    var colors = ["#4f6d7a", "#b55239", "#7b6d52", "#8b9d77", "#a37b5c"];
    chart.setOption({
        tooltip: { show: true },
        series: [{
            type: "wordCloud", shape: "circle", gridSize: 8,
            sizeRange: [14, 54], rotationRange: [0, 0],
            textStyle: {
                fontFamily: "Microsoft YaHei",
                color: function () { return colors[Math.floor(Math.random() * colors.length)]; }
            },
            data: (data || []).map(function (item) {
                return { name: item.name, value: Math.max(1, Math.round(item.value * 1000)) };
            })
        }]
    });
}

function drawgraph(id, nodes, links) {
    var chart = echarts.init(document.getElementById(id));
    chart.setOption({
        tooltip: { formatter: "{b}" },
        series: [{
            type: "graph", layout: "force", roam: true,
            data: nodes || [], links: links || [],
            label: { show: true, position: "right", fontSize: 12 },
            force: { repulsion: 300, edgeLength: 120 },
            lineStyle: { color: "#b9ad98", width: 1, curveness: 0.1 },
            itemStyle: { color: "#7b6d52" }
        }]
    });
}
