package main

/*
.SYNOPSIS

.DESCRIPTION
Uses Pulumi service API to collect resource usage metrics for a given organization.
The output it produces represents the resources deployed using the Pulumi service at that moment in time.
It does not provide any historical information.

This tool uses the Pulumi service API to read the data.

.EXAMPLE
pulumi-rum-counter -service_host mypulumi.com -access_token pul-12345456 -org acme

.PARAMETER service_host
The pulumi service host name. For example, for the Pulumi SaaS this would be pulumi.com.

.PARAMETER access_token
A Pulumi access token that has access to the specified organization.

.PARAMETER org
The pulumi organization from which to gather the metrics.

CROSS-COMPLIATION NOTES
env GOOS=windows GOARCH=amd64 go build ./pulumi-rum-counter.go

*/

import (
	// "bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	// "mime/multipart"
	"net/http"
	// "strings"

	// // used if debugging http "net/http/httputil"
	"crypto/tls"
	"flag"
	"os"
	"time"
	//"reflect"
)

type Project struct {
	orgName     string
	projectName string
	repoName    string
	runTime     string
	stacks      []Stack
}

type Stack struct {
	stackName           string
	lastUpdateStartTime int
	lastUpdateResult    string
	resourceCount       int
}

type RumMetrics struct {
	totalRum     int
	stackMetrics []StackMetric
}
type StackMetric struct {
	stackName string
	rum       int
}

func main() {

	// 0.1 version: Initial version
	version := "0.1"
	fmt.Println("pulumi-rum-counter version " + version)

	// Process command line arguments
	service_host := flag.String("service_host", "", "Pulumi service host name or IP")
	access_token := flag.String("access_token", "", "Pulumi access token with access to specified Organization")
	org := flag.String("org", "", "Pulumi organization from which to gather resource counts.")

	flag.Parse()

	if (*access_token == "") || (*org == "") {
		fmt.Println("*************")
		fmt.Println("Missing command line argument ...")
		fmt.Println("Run \"" + os.Args[0] + " -h\" for more information.")
		fmt.Println("*************")
		os.Exit(1)
	}

	if *service_host == "" {
		fmt.Println("Defaulting to use Pulumi SaaS at pulumi.com")
		fmt.Println("Specify -service_host parameter for self-hosted service.")
		*service_host = "pulumi.com"
	}

	// end command line arguments

	// 	// Call Turbo to get any host-level actions for the servers assigned to each application
	// 	fmt.Printf("*** Getting host actions from Turbo for clusters in group, %s ...\n", *cluster_group)
	// 	clusterActionsMap, clusterNameMap := getHostActions(*turbo_instance, *turbo_user, *turbo_password, *cluster_group)

	time_now := time.Now().Format(time.RFC3339)
	fmt.Printf("Gathering RUM data as of %s\n", time_now)

	getRumMetrics(*service_host, *access_token, *org)

	fmt.Println("Done.")
}

func getRumMetrics(service_host string, access_token string, org string) RumMetrics {
	rumMetrics := new(RumMetrics)
	rumMetrics.totalRum = 99999
	_ = getProjects(service_host, access_token, org)
	return *rumMetrics
}

func getProjects(service_host string, access_token string, org string) []Project {

	projects := new([]Project)

	url := "https://api." + service_host + "/api/console/orgs/" + org + "/repos"
	method := "GET"

	customTransport := http.DefaultTransport.(*http.Transport).Clone()
	customTransport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true}
	client := &http.Client{Transport: customTransport}

	// create and make the request
	req, err := http.NewRequest(method, url, nil)
	if err != nil {
		fmt.Println(err)
	}
	req.Header.Add("Authorization", "token "+access_token)
	res, err := client.Do(req)
	if err != nil {
		fmt.Println(err)
		os.Exit(3)
	}

	defer res.Body.Close()
	// essentially creates a stringified version of the body's json
	body, _ := ioutil.ReadAll(res.Body)
	fmt.Println(string(body))

	// Since the search results is a json with an array of json,
	// Create an array of one of these interface things to unmarshal the stringified json into
	var searchResults map[string]interface{}
	err = json.Unmarshal([]byte(body), &searchResults)
	if err != nil {
		fmt.Println(err)
		os.Exit(4)
	}
	// now searchResults is json an array of structures that we can index.
	// There's only one result so we're hardcoding the array index and we only care about the uuid
	fmt.Println("searchResults")
	fmt.Println(searchResults)

	if len(searchResults) > 0 {
		return searchResults.(string)
	} else {
		return "NOTFOUND"
	}

	return *projects
}

// // Using the data found in the various maps, assemble API calls to push PowerBi to push the data stream
// func pushPowerBiData(clusterNameMap map[string]string, clusterActionsMap map[string][]Action, powerbi_url string) {

// 	t := time.Now()
// 	timeString := t.Format(time.RFC3339)
// 	method := "POST"

// 	apiCount := 0
// 	for clusterUuid, clusterName := range clusterNameMap {
// 		var payload string
// 		action_count := 0
// 		apiCount++
// 		for _, action := range clusterActionsMap[clusterUuid] {
// 			timestamp_part := "\"Timestamp\": \"" + timeString + "\""
// 			clustername_part := "\"Cluster_Name\": \"" + clusterName + "\""
// 			entityname_part := "\"Entity_Name\": \"" + action.entityName + "\""
// 			entitytype_part := "\"Entity_Type\": \"" + action.entityType + "\""
// 			actiontype_part := "\"Action_Type\": \"" + action.actionType + "\""
// 			actiondetails_part := "\"Action_Details\": \"" + action.actionDetails + "\""
// 			//actionfrom_part := "\"Action_From\": \""+action.actionFrom+"\""
// 			//actionto_part := "\"Action_To\": \""+action.actionTo+"\""
// 			reason_part := "\"Reason\": \"" + action.reason + "\""
// 			severity_part := "\"Severity\": \"" + action.severity + "\""
// 			category_part := "\"Category\": \"" + action.category + "\""

// 			//action_payload := "{"+timestamp_part+","+clustername_part+","+entityname_part+","+entitytype_part+","+actiondetails_part+","+actiontype_part+","+actionfrom_part+","+actionto_part+","+reason_part+","+severity_part+","+category_part+"}"
// 			action_payload := "{" + timestamp_part + "," + clustername_part + "," + entityname_part + "," + entitytype_part + "," + actiondetails_part + "," + actiontype_part + "," + reason_part + "," + severity_part + "," + category_part + "}"
// 			action_count++
// 			if payload == "" {
// 				payload = "[" + action_payload
// 			} else {
// 				payload = payload + "," + action_payload
// 			}
// 		}
// 		payload = payload + "]"

// 		if action_count > 0 {
// 			client := &http.Client{}
// 			req, err := http.NewRequest(method, powerbi_url, strings.NewReader(payload))
// 			if err != nil {
// 				fmt.Println(err)
// 			}
// 			req.Header.Add("Content-Type", "application/json")

// 			// 		// For debugging HTTP Call
// 			// 		requestDump, err := httputil.DumpRequest(req, true)
// 			// 		if err != nil {
// 			// 				fmt.Println(err)
// 			// 		}
// 			// 		fmt.Println(string(requestDump))
// 			// 		// END DEBUGGING

// 			res, _ := client.Do(req)
// 			defer res.Body.Close()

// 			if res.StatusCode != 200 {
// 				fmt.Printf("### ERROR ### sending %d records for cluster %s\n", action_count, clusterName)
// 				fmt.Println("### HTML ERROR ### ", res.StatusCode, http.StatusText(res.StatusCode))
// 			} else {
// 				fmt.Printf("... sent %d records(s) for cluster %s\n", action_count, clusterName)
// 			}

// 			if (apiCount % 110) == 0 {
// 				fmt.Printf(" ... made %d API calls. Sleeping for 1 minute to avoid overloading PowerBI API limits ...", apiCount)
// 				time.Sleep(1 * time.Minute)
// 			}
// 		}
// 	}
// }

// // Calls Turbo Actions API to get all resize actions currently identified by Turbo.
// // Returns:
// // - map: Cluster UUID -> Cluster Name
// // - map: Cluster UUID -> actions
// func getHostActions(turbo_instance string, turbo_user string, turbo_password string, cluster_group_name string) (map[string][]Action, map[string]string) {

// 	// get auth token
// 	auth := turboLogin(turbo_instance, turbo_user, turbo_password)

// 	fmt.Printf("... getting cluster list for group, %s ...\n", cluster_group_name)
// 	// Find the UUID for the group
// 	group_uuid := getGroupId(turbo_instance, cluster_group_name, auth)
// 	// Use the Group UUID to get the cluster members of the group
// 	clusterNameMap := getGroupMembers(turbo_instance, auth, group_uuid)

// 	// Get the host actions for each cluster and build a map of cluster UUID to actions
// 	var clusterActionsMap map[string][]Action
// 	clusterActionsMap = make(map[string][]Action)
// 	for clusterUuid, clusterName := range clusterNameMap {
// 		fmt.Printf("... getting actions for cluster, %s ...\n", clusterName)

// 		base_url := "https://" + turbo_instance + "/vmturbo/rest/groups/" + clusterUuid + "/actions"
// 		url := base_url
// 		method := "GET"

// 		done := false
// 		for !done {

// 			customTransport := http.DefaultTransport.(*http.Transport).Clone()
// 			customTransport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true}
// 			client := &http.Client{Transport: customTransport}
// 			req, err := http.NewRequest(method, url, nil)
// 			if err != nil {
// 				fmt.Println(err)
// 			}
// 			req.Header.Add("Content-Type", "application/json")
// 			req.Header.Add("Cookie", auth)

// 			// 			// For debugging HTTP Call
// 			// 			requestDump, err := httputil.DumpRequest(req, true)
// 			// 			if err != nil {
// 			//   				fmt.Println(err)
// 			// 			}
// 			// 			fmt.Println(string(requestDump))

// 			res, err := client.Do(req)
// 			if err != nil {
// 				fmt.Println(err)
// 				os.Exit(3)
// 			}

// 			defer res.Body.Close()
// 			// essentially creates a stringified version of the body's json
// 			body, _ := ioutil.ReadAll(res.Body)

// 			// Since the results is an array of json,
// 			// Create an array of one of these interface things to unmarshal the stringified json into
// 			var responseActions []map[string]interface{}
// 			err = json.Unmarshal([]byte(body), &responseActions)

// 			if err != nil {
// 				fmt.Println(err)
// 				fmt.Printf("#### ERROR decoding response: %v\n", err)
// 				if e, ok := err.(*json.SyntaxError); ok {
// 					fmt.Printf("#### ERROR syntax error at byte offset %d\n", e.Offset)
// 				}
// 				fmt.Printf("#### ERROR response: %q\n", body)
// 			}

// 			var allActions []Action
// 			for _, responseAction := range responseActions {
// 				var action Action

// 				action.actionUuid = responseAction["uuid"].(string)
// 				action.actionType = responseAction["actionType"].(string)
// 				action.reason = responseAction["risk"].(map[string]interface{})["description"].(string)
// 				action.severity = responseAction["risk"].(map[string]interface{})["severity"].(string)
// 				action.category = responseAction["risk"].(map[string]interface{})["subCategory"].(string)
// 				action.actionDetails = responseAction["details"].(string)
// 				action.entityType = responseAction["target"].(map[string]interface{})["className"].(string)
// 				action.entityName = responseAction["target"].(map[string]interface{})["displayName"].(string)

// 				allActions = append(clusterActionsMap[clusterUuid], action)
// 				clusterActionsMap[clusterUuid] = allActions
// 			}

// 			// Are there more actions to get from the API?
// 			cursor := res.Header.Get("x-next-cursor")
// 			if len(cursor) > 0 {
// 				url = base_url + "?cursor=" + cursor
// 				fmt.Printf("... still getting actions for cluster %s (cursor=%s) ...\n", clusterName, cursor)
// 			} else {
// 				done = true
// 				//fmt.Println("DONE GETTING ACTIONS")
// 			}
// 		}
// 	}

// 	return clusterActionsMap, clusterNameMap
// }

// // Get Group Members
// func getGroupMembers(turbo_instance string, auth string, group_uuid string) map[string]string {

// 	var clusterNameMap map[string]string
// 	clusterNameMap = make(map[string]string)

// 	url := "https://" + turbo_instance + "/vmturbo/rest/groups/" + group_uuid + "/members"
// 	method := "GET"

// 	customTransport := http.DefaultTransport.(*http.Transport).Clone()
// 	customTransport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true}
// 	client := &http.Client{Transport: customTransport}

// 	// create and make the request
// 	req, err := http.NewRequest(method, url, nil)
// 	if err != nil {
// 		fmt.Println(err)
// 	}
// 	req.Header.Add("Content-Type", "application/json")
// 	req.Header.Add("Cookie", auth)
// 	res, err := client.Do(req)
// 	if err != nil {
// 		fmt.Println(err)
// 		os.Exit(3)
// 	}

// 	defer res.Body.Close()
// 	// essentially creates a stringified version of the body's json
// 	body, _ := ioutil.ReadAll(res.Body)

// 	// Since the results is an array of json,
// 	// Create an array of one of these interface things to unmarshal the stringified json into
// 	var jsonBody []map[string]interface{}
// 	err = json.Unmarshal([]byte(body), &jsonBody)

// 	if err != nil {
// 		fmt.Println(err)
// 		fmt.Printf("#### ERROR decoding response: %v\n", err)
// 		if e, ok := err.(*json.SyntaxError); ok {
// 			fmt.Printf("#### ERROR syntax error at byte offset %d\n", e.Offset)
// 		}
// 		fmt.Printf("#### ERROR response: %q\n", body)
// 	}

// 	for _, groupMember := range jsonBody {
// 		clusterUuid := groupMember["uuid"].(string)
// 		clusterNameMap[clusterUuid] = groupMember["displayName"].(string)
// 	}

// 	return clusterNameMap
// }

// get Group UUID

// 	defer res.Body.Close()
// 	// essentially creates a stringified version of the body's json
// 	body, _ := ioutil.ReadAll(res.Body)
// 	//fmt.Println(string(body))

// 	// Since the search results is an array of json,
// 	// Create an array of one of these interface things to unmarshal the stringified json into
// 	var searchResults []map[string]interface{}
// 	err = json.Unmarshal([]byte(body), &searchResults)
// 	if err != nil {
// 		fmt.Println(err)
// 		os.Exit(4)
// 	}
// 	// now searchResults is an array of structures that we can index.
// 	// There's only one result so we're hardcoding the array index and we only care about the uuid
// 	//fmt.Println("searchResults")
// 	//fmt.Println(searchResults)

// 	if len(searchResults) > 0 {
// 		return searchResults[0]["uuid"].(string)
// 	} else {
// 		return "NOTFOUND"
// 	}
// }

// // Login to turbo
// func turboLogin(turbo_instance string, turbo_user string, turbo_password string) string {

// 	fmt.Println("... authenticating to Turbonomic instance, " + turbo_instance)

// 	url := "https://" + turbo_instance + "/vmturbo/rest/login"
// 	method := "POST"

// 	payload := &bytes.Buffer{}
// 	writer := multipart.NewWriter(payload)
// 	_ = writer.WriteField("username", turbo_user)
// 	_ = writer.WriteField("password", turbo_password)
// 	err := writer.Close()
// 	if err != nil {
// 		fmt.Println(err)
// 		os.Exit(2)
// 	}

// 	// set up the request client to ignore self-signed cert from Turbo
// 	customTransport := http.DefaultTransport.(*http.Transport).Clone()
// 	customTransport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true}
// 	client := &http.Client{Transport: customTransport}

// 	req, err := http.NewRequest(method, url, payload)
// 	if err != nil {
// 		fmt.Println(err)
// 	}
// 	req.Header.Set("Content-Type", writer.FormDataContentType())
// 	res, err := client.Do(req) // send the post request, "res" has the response
// 	if err != nil {
// 		fmt.Println(err)
// 	}
// 	defer res.Body.Close()
// 	//body, err := ioutil.ReadAll(res.Body)
// 	//fmt.Println(string(body))

// 	// get the jsessionid cookie for subsequent requests
// 	// This is inelegant code at this time that relies on knowing there is one cookie, the first part of which is the jsessionID bit
// 	cookie := res.Cookies()
// 	jsessionid_cookie := cookie[0].Name + "=" + cookie[0].Value

// 	return jsessionid_cookie
// }
