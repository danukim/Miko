using UnityEngine;
using VRM;

public class LookAtAnimationBlender : MonoBehaviour
{
    [SerializeField]
    private Animator animator;

    [SerializeField]
    private VRMLookAtBoneApplyer boneApplyer;

    [SerializeField]
    private string[] targetAnimationStateNames = {"Idle Look Left And Right", "Idle Stretch", "Idle Look At Hands", "Idle Look At Feet", "Shaking head"};

    [SerializeField, Range(0.1f, 10f)]
    private float transitionSpeed = 2.0f;

    private void Start()
    {
        if (animator == null)
        {
            animator = GetComponent<Animator>();
        }

        if (boneApplyer == null)
        {
            boneApplyer = GetComponent<VRMLookAtBoneApplyer>();
        }

        if (boneApplyer == null)
        {
            Debug.LogError("[LookAtAnimationBlender] VRMLookAtBoneApplyer not found!");
            enabled = false;
        }
    }

    private void Update()
    {
        if (boneApplyer == null || animator == null) return;

        AnimatorStateInfo stateInfo = animator.GetCurrentAnimatorStateInfo(0);
        bool isPlayingTargetAnimation = IsPlayingTargetAnimation(stateInfo);
        
        float targetWeight = isPlayingTargetAnimation ? 0.0f : 1.0f;

        boneApplyer.HeadTrackingWeight = Mathf.MoveTowards(
            boneApplyer.HeadTrackingWeight, 
            targetWeight, 
            transitionSpeed * Time.deltaTime
        );
    }

    private bool IsPlayingTargetAnimation(AnimatorStateInfo stateInfo)
    {
        foreach (var stateName in targetAnimationStateNames)
        {
            if (stateInfo.IsName(stateName))
            {
                return true;
            }
        }
        return false;
    }
}
