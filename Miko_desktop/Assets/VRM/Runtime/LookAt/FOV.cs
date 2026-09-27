using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace VRM
{
    public class FOV : MonoBehaviour
    {
        // Add this field to store the target object
        public GameObject targetObject;

        // Add this field to store whether the target is in the collider
        public bool isTargetInCollider = false;

        public bool IsTargetInCollider()
        {
            return isTargetInCollider;
        }

        // Start is called before the first frame update
        void Start()
        {
            // Ensure the collider is set as a trigger
            GetComponent<Collider>().isTrigger = true;

            // Check if the target is inside the collider at the start
            Collider[] colliders = Physics.OverlapSphere(transform.position, GetComponent<Collider>().bounds.extents.magnitude);
            foreach (Collider collider in colliders)
            {
                if (collider.gameObject == targetObject)
                {
                    isTargetInCollider = true;
                    break;
                }
            }
        }

        // Update is called once per frame
        void Update()
        {
            // You can check the isTargetInCollider flag here
            if (isTargetInCollider)
            {
                Debug.Log("Target is in the collider");
            }
            else
            {
                Debug.Log("Target is not in the collider");
            }
        }

        // Add these methods to detect when the target enters and leaves the collider
        private void OnTriggerEnter(Collider other)
        {
            if (other.gameObject == targetObject)
            {
                isTargetInCollider = true;
            }
        }

        private void OnTriggerExit(Collider other)
        {
            if (other.gameObject == targetObject)
            {
                isTargetInCollider = false;
            }
        }
    }
}