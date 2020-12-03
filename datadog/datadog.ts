import * as datadog from "@pulumi/datadog";

interface TargetType {
  hostName: string;
  hostId: string;
}

export function setupDatadog(target: TargetType) {
  const hostName = target["hostName"]
  const hostId = target["hostId"]

  // Create Datadog Monitor for the Instance just created
  const ddogMonitor = new datadog.Monitor("ddog-monitor", {
    name: hostName+"-cpu",
    message: hostName+"-cpu Monitor",
    type: "metric alert",
    query: "avg(last_1m):avg:datadog.trace_agent.cpu_percent{host:"+hostId+"} > 10"
  })

  // Create Datadog Dashboard that pulls together data from the monitor and the host.
  const ddogDashboard = new datadog.Dashboard("ddog-dashboard", {
    layoutType: "ordered",
    title: "Pulumi Created Dashboard",
    widgets: [
        {
            alertValueDefinition: {
            "alertId": ddogMonitor.id,
            "title": ddogMonitor.name,
            "titleSize": "16",
            "titleAlign": "left",
            "unit": "auto",
            "textAlign": "left",
            "precision": 2
            },
        },
        {
            timeseriesDefinition: {
            "title": "Avg of CPU Utilization over host:"+hostId,
            "titleSize": "16",
            "titleAlign": "left",
            "showLegend": false,
            "time": {},
            "requests": [
              {
                "q": "avg:system.cpu.user{host:"+hostId+"}",
                "style": {
                  "palette": "dog_classic",
                  "lineType": "solid",
                  "lineWidth": "normal"
                },
                "displayType": "line"
              }
            ],
            "yaxis": {
              "scale": "linear",
              "label": "",
              "includeZero": true,
              "min": "auto",
              "max": "auto"
            },
            "markers": []
          }
        }
    ]
  })
}