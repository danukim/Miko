using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Look : MonoBehaviour
{
    public GameObject target; // reference to the Target gameobject
    public Vector3 defaultPosition; // default position for the target

    private bool isTargetInCollider = false;

    private void Start()
    {
        // Check if the target is already in the collider when the game starts
        Collider collider = GetComponent<Collider>();
        if (collider.bounds.Contains(target.transform.position))
        {
            isTargetInCollider = true;
        }
    }

    private void Update()
    {
        MoveTargetLookAt();
    }

    private void OnTriggerEnter(Collider other)
    {
        if (other.gameObject == target)
        {
            isTargetInCollider = true;
        }
    }

    private void OnTriggerExit(Collider other)
    {
        if (other.gameObject == target)
        {
            isTargetInCollider = false;
        }
    }

    private void MoveTargetLookAt()
    {
        if (isTargetInCollider)
        {
            // If target is in the collider, move it to the target's position
            target.transform.position = target.transform.position;
			Debug.Log("target is in the collider");
        }
        else
        {
            // If target is not in the collider, move it back to the default position
            target.transform.position = defaultPosition;
			Debug.Log("target is not in the collider");
        }
    }
}