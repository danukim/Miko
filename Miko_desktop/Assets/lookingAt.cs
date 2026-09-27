using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

public class RaycastController : MonoBehaviour
{
    private const string serverUrl = "http://192.168.0.22:8000/uploaded_files/";
    private string messageToSend = "NoFocus";
    private string lastMessageSent = "";

    void Update()
    {
        Ray ray = new Ray(transform.position, transform.forward);
        RaycastHit hit;

        if (Physics.Raycast(ray, out hit))
        {
            // Handle the collision
            CheckCollision(hit.collider.gameObject);
        }
    }

    void CheckCollision(GameObject hitObject)
    {
        if (hitObject.name == "MITSUHA_Default")
        {
            Debug.Log("<color=blue>Looking at MITSUHA</color>");
            messageToSend = "Focus";
        }
        else
        {
            Debug.Log("Not looking at MITSUHA");
            messageToSend = "NoFocus";
        }

        // Only send the message if it's different from the last one sent
        if (messageToSend != lastMessageSent)
        {
            // Send the POST request
            Debug.Log("Sending message: " + messageToSend);
            StartCoroutine(SendPostRequest());

            // Update the last message sent
            lastMessageSent = messageToSend;
        }
    }

    IEnumerator SendPostRequest()
    {
        // Create a form with the message data
        WWWForm form = new WWWForm();
        form.AddField("message", messageToSend);

        // Send the POST request using UnityWebRequest
        using (UnityWebRequest www = UnityWebRequest.Post(serverUrl, form))
        {
            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                Debug.Log("<color=blue>Message sent successfully!</color>");
            }
            else
            {
                Debug.LogError("<color=red>Failed to send message: </color>" + www.error);
            }
        }
    }
}