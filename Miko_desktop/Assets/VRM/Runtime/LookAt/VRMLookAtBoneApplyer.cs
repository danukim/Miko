//You can simply copy and paste this entire script if you want to skip the tutorial
//Just do a Ctrl + A on your Visual Studio, and paste (Ctrl + V)

#pragma warning disable 0414, 0649
using UniGLTF;
using UnityEngine;

namespace VRM
{
    public class VRMLookAtBoneApplyer : MonoBehaviour, IVRMComponent
    {
        public bool DrawGizmo = false;

        [SerializeField]
        public OffsetOnTransform LeftEye;

        [SerializeField]
        public OffsetOnTransform RightEye;

        //Added Head for Head tracking
        public Transform head;

        [Range(0, 1)]
        public float HeadTrackingWeight = 1.0f;

        [SerializeField, Header("Degree Mapping")]
        public CurveMapper HorizontalOuter = new CurveMapper(90.0f, 10.0f);

        [SerializeField]
        public CurveMapper HorizontalInner = new CurveMapper(90.0f, 10.0f);

        [SerializeField]
        public CurveMapper VerticalDown = new CurveMapper(90.0f, 10.0f);

        [SerializeField]
        public CurveMapper VerticalUp = new CurveMapper(90.0f, 10.0f);

        public void OnImported(VRMImporterContext context)
        {
            var animator = GetComponent<Animator>();
            if (animator != null)
            {
                LeftEye = OffsetOnTransform.Create(animator.GetBoneTransform(HumanBodyBones.LeftEye));
                RightEye = OffsetOnTransform.Create(animator.GetBoneTransform(HumanBodyBones.RightEye));
            }

            var gltfFirstPerson = context.VRM.firstPerson;
            HorizontalInner.Apply(gltfFirstPerson.lookAtHorizontalInner);
            HorizontalOuter.Apply(gltfFirstPerson.lookAtHorizontalOuter);
            VerticalDown.Apply(gltfFirstPerson.lookAtVerticalDown);
            VerticalUp.Apply(gltfFirstPerson.lookAtVerticalUp);
        }

        private void OnValidate()
        {
            HorizontalInner.OnValidate();
            HorizontalOuter.OnValidate();
            VerticalUp.OnValidate();
            VerticalDown.OnValidate();
        }

        VRMLookAtHead m_head;

        void Start()
        {
            m_head = GetComponent<VRMLookAtHead>();
            if (m_head == null)
            {
                enabled = false;
                Debug.LogError("[VRMLookAtBoneApplyer]VRMLookAtHead not found");
                return;
            }
            m_head.YawPitchChanged += ApplyRotations;
            LeftEye.Setup();
            RightEye.Setup();
        }

        #region Gizmo
        static void DrawMatrix(Matrix4x4 m, float size)
        {
            Gizmos.matrix = m;
            Gizmos.color = Color.red;
            Gizmos.DrawLine(Vector3.zero, Vector3.right * size);
            Gizmos.color = Color.green;
            Gizmos.DrawLine(Vector3.zero, Vector3.up * size);
            Gizmos.color = Color.blue;
            Gizmos.DrawLine(Vector3.zero, Vector3.forward * size);
        }

        const float SIZE = 0.5f;

        private void OnDrawGizmos()
        {
            if (DrawGizmo)
            {
                if (LeftEye.Transform != null & RightEye.Transform != null)
                {
                    DrawMatrix(LeftEye.WorldMatrix, SIZE);
                    DrawMatrix(RightEye.WorldMatrix, SIZE);
                }
            }
        }
        #endregion

        void ApplyRotations(float yaw, float pitch)
        {
            // horizontal
            float leftYaw, rightYaw;
            if (yaw < 0)
            {
                leftYaw = -HorizontalOuter.Map(-yaw);
                rightYaw = -HorizontalInner.Map(-yaw);
            }
            else
            {
                rightYaw = HorizontalOuter.Map(yaw);
                leftYaw = HorizontalInner.Map(yaw);
            }

            // vertical
            if (pitch < 0)
            {
                pitch = -VerticalDown.Map(-pitch);
            }
            else
            {
                pitch = VerticalUp.Map(pitch);
            }

            // Apply
            if (LeftEye.Transform != null && RightEye.Transform != null)
            {
                // 目に値を適用する
                LeftEye.Transform.rotation = LeftEye.InitialWorldMatrix.ExtractRotation() * Matrix4x4.identity.YawPitchRotation(leftYaw, pitch);
                RightEye.Transform.rotation = RightEye.InitialWorldMatrix.ExtractRotation() * Matrix4x4.identity.YawPitchRotation(rightYaw, pitch);
            }

            //Added Head for Head tracking
            if(head != null && m_head.Target != null)
            {
                // Calculate the rotation required to look at the target in world space
                Vector3 direction = m_head.Target.position - head.position;
                if (direction != Vector3.zero)
                {
                    Quaternion targetRotation = Quaternion.LookRotation(direction, Vector3.up);
                    // Smoothly blend between the current rotation (from animation) and the target look rotation
                    head.rotation = Quaternion.Slerp(head.rotation, targetRotation, HeadTrackingWeight);
                }
            }
        }
    }
}
