(function () {
    "use strict";

    if (typeof window.echarts === "undefined") {
        return;
    }

    var reduceMotion =
        window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function readPayload(id) {
        var node = document.getElementById(id);
        if (!node) {
            return null;
        }
        try {
            return JSON.parse(node.textContent);
        } catch (error) {
            return null;
        }
    }

    function colors() {
        var styles = window.getComputedStyle(document.documentElement);
        function read(name, fallback) {
            var value = styles.getPropertyValue(name);
            return value ? value.trim() : fallback;
        }
        return {
            paper: read("--paper", "#f6f1e7"),
            paperDeep: read("--paper-deep", "#ece4d4"),
            ink: read("--ink", "#2f352c"),
            muted: read("--muted", "#6f7b72"),
            line: read("--line", "#d8cfbd"),
            lineStrong: read("--line-strong", "#c4b8a1"),
            ochre: read("--ochre", "#8c5f3b"),
            celadon: read("--celadon", "#6f7b72")
        };
    }

    function geoStyle(theme) {
        return {
            map: "china",
            roam: false,
            itemStyle: {
                areaColor: theme.paperDeep,
                borderColor: theme.line
            },
            emphasis: {
                itemStyle: { areaColor: theme.paper },
                label: { color: theme.ink }
            },
            label: { show: false }
        };
    }

    function distributionOption(data, theme) {
        return {
            backgroundColor: "transparent",
            tooltip: {
                trigger: "item",
                formatter: function (params) {
                    return (
                        params.name +
                        "：" +
                        params.value +
                        "<br>示意强度（0–100），非人口占比"
                    );
                }
            },
            visualMap: {
                min: 0,
                max: 100,
                left: "left",
                bottom: 10,
                text: ["强", "弱"],
                inRange: { color: [theme.paperDeep, theme.ochre] },
                textStyle: { color: theme.muted }
            },
            series: [
                {
                    type: "map",
                    map: "china",
                    roam: false,
                    label: { show: false },
                    itemStyle: { areaColor: "transparent", borderColor: theme.line },
                    emphasis: {
                        label: { show: true, color: theme.ink },
                        itemStyle: { areaColor: theme.paperDeep }
                    },
                    data: data
                }
            ]
        };
    }

    function migrationOptions(events, theme) {
        var options = events.map(function (event) {
            var series = [];
            if (event.from_coord && event.to_coord) {
                series.push({
                    type: "lines",
                    coordinateSystem: "geo",
                    zlevel: 2,
                    data: [{ coords: [event.from_coord, event.to_coord] }],
                    lineStyle: {
                        color: theme.ochre,
                        width: 2,
                        curveness: 0.2
                    },
                    effect: {
                        show: !reduceMotion,
                        period: 4,
                        trailLength: 0.3,
                        symbolSize: 4,
                        color: theme.ochre
                    }
                });
            }
            if (event.from_coord) {
                series.push({
                    type: "scatter",
                    coordinateSystem: "geo",
                    zlevel: 3,
                    symbolSize: 7,
                    itemStyle: { color: theme.celadon },
                    data: [{ name: event.from_name, value: event.from_coord }]
                });
            }
            if (event.to_coord) {
                series.push({
                    type: "scatter",
                    coordinateSystem: "geo",
                    zlevel: 3,
                    symbolSize: 9,
                    itemStyle: { color: theme.ochre },
                    data: [{ name: event.to_name, value: event.to_coord }]
                });
            }
            return {
                backgroundColor: "transparent",
                title: {
                    text: event.dynasty,
                    subtext: event.description,
                    left: "center",
                    textStyle: { color: theme.ink, fontSize: 14 },
                    subtextStyle: { color: theme.muted, fontSize: 12 }
                },
                tooltip: {
                    trigger: "item",
                    formatter: function (params) {
                        return params.name || event.description;
                    }
                },
                geo: geoStyle(theme),
                series: series
            };
        });

        return {
            backgroundColor: "transparent",
            baseOption: {
                timeline: {
                    axisType: "category",
                    autoPlay: false,
                    playInterval: 4000,
                    left: 40,
                    right: 40,
                    bottom: 0,
                    data: events.map(function (event, index) {
                        return event.dynasty + " · " + (index + 1);
                    }),
                    label: { color: theme.muted },
                    lineStyle: { color: theme.line },
                    checkpointStyle: { color: theme.ochre },
                    controlStyle: { color: theme.ochre, borderColor: theme.ochre }
                }
            },
            options: options
        };
    }

    function relationsOption(payload, theme) {
        return {
            backgroundColor: "transparent",
            tooltip: {
                formatter: function (params) {
                    if (params.dataType === "edge") {
                        return params.data.labelText || "";
                    }
                    return params.name;
                }
            },
            legend: {
                data: payload.categories.map(function (category) {
                    return category.name;
                }),
                bottom: 0,
                textStyle: { color: theme.ink }
            },
            series: [
                {
                    type: "graph",
                    layout: "force",
                    roam: true,
                    draggable: true,
                    edgeSymbol: ["none", "arrow"],
                    edgeSymbolSize: 6,
                    categories: payload.categories,
                    force: { repulsion: 220, edgeLength: 120 },
                    label: { show: true, color: theme.ink },
                    lineStyle: { color: theme.lineStrong, width: 1.4 },
                    emphasis: { focus: "adjacency" },
                    data: payload.nodes.map(function (node) {
                        return {
                            name: node.name,
                            category: node.category,
                            symbolSize: node.slug ? 42 : 32,
                            itemStyle: {
                                color: node.category === 0 ? theme.ochre : theme.celadon
                            }
                        };
                    }),
                    links: payload.edges.map(function (edge) {
                        return {
                            source: edge.source,
                            target: edge.target,
                            labelText: edge.label,
                            label: {
                                show: true,
                                formatter: edge.label,
                                color: theme.muted,
                                fontSize: 11
                            }
                        };
                    })
                }
            ]
        };
    }

    function keywordsOption(keywords, theme) {
        var palette = [theme.ochre, theme.celadon, theme.ink, theme.muted];
        return {
            backgroundColor: "transparent",
            tooltip: {
                formatter: function (params) {
                    return params.name + "：" + params.value + "（演示权重）";
                }
            },
            series: [
                {
                    type: "wordCloud",
                    shape: "circle",
                    sizeRange: [12, 46],
                    rotationRange: [-30, 30],
                    gridSize: 8,
                    drawOutOfBound: false,
                    textStyle: {
                        fontFamily: "system-ui, sans-serif",
                        color: function () {
                            return palette[Math.floor(Math.random() * palette.length)];
                        }
                    },
                    data: keywords
                }
            ]
        };
    }

    var registry = [];

    function initChart(element) {
        if (element.dataset.chartInitialized === "true") {
            return;
        }
        var canvas = element.querySelector("[data-chart-canvas]");
        if (!canvas) {
            return;
        }
        var kind = element.dataset.chart;
        var theme = colors();
        var option;
        var clickHandler = null;

        if (kind === "distribution") {
            var distribution = readPayload("distribution-data");
            if (!distribution || !distribution.length) {
                return;
            }
            option = function () {
                return distributionOption(distribution, colors());
            };
        } else if (kind === "migration") {
            var migration = readPayload("migration-data");
            if (!migration || !migration.length) {
                return;
            }
            option = function () {
                return migrationOptions(migration, colors());
            };
        } else if (kind === "relations" || kind === "origins") {
            var graph = readPayload(
                kind === "relations" ? "relations-data" : "origins-data"
            );
            if (!graph || !graph.nodes || !graph.nodes.length) {
                return;
            }
            option = function () {
                return relationsOption(graph, colors());
            };
            var base = element.dataset.detailBase || "/surname/";
            var slugs = {};
            graph.nodes.forEach(function (node) {
                if (node.slug) {
                    slugs[node.name] = node.slug;
                }
            });
            clickHandler = function (params) {
                if (params.dataType === "node" && slugs[params.name]) {
                    window.location.href =
                        base + encodeURIComponent(slugs[params.name]) + "/";
                }
            };
        } else if (kind === "keywords") {
            var keywords = readPayload("keywords-data");
            if (!keywords || !keywords.length) {
                return;
            }
            option = function () {
                return keywordsOption(keywords, colors());
            };
        } else {
            return;
        }

        var instance;
        if (kind === "keywords") {
            try {
                instance = window.echarts.init(canvas);
                instance.setOption(option(), true);
            } catch (error) {
                if (instance) {
                    instance.dispose();
                }
                canvas.textContent = "词云组件不可用，请查看下方关键词列表。";
                element.dataset.chartInitialized = "true";
                return;
            }
        } else {
            instance = window.echarts.init(canvas);
            instance.setOption(option(), true);
        }

        if (clickHandler) {
            instance.on("click", clickHandler);
        }
        element.dataset.chartInitialized = "true";
        registry.push({ element: element, instance: instance, option: option });
    }

    function initVisibleCharts() {
        document.querySelectorAll("[data-chart]").forEach(initChart);
    }

    function observeCharts() {
        var elements = document.querySelectorAll("[data-chart]");
        if (!("IntersectionObserver" in window)) {
            elements.forEach(initChart);
            return;
        }
        var observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        initChart(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            },
            { rootMargin: "200px" }
        );
        elements.forEach(function (element) {
            observer.observe(element);
        });
    }

    window.addEventListener("themechange", function () {
        registry.forEach(function (entry) {
            entry.instance.setOption(entry.option(), true);
        });
    });

    var resizeTimer = null;
    window.addEventListener("resize", function () {
        window.clearTimeout(resizeTimer);
        resizeTimer = window.setTimeout(function () {
            registry.forEach(function (entry) {
                entry.instance.resize();
            });
        }, 150);
    });

    window.ShiyuanCharts = { initCharts: initVisibleCharts };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", observeCharts);
    } else {
        observeCharts();
    }
})();
