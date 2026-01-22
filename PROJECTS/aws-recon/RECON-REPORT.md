# AWS Brandpoint Account Reconnaissance Report

**Account ID:** 144105412483
**Region:** us-east-1
**User:** codename37
**Date:** 2026-01-21

---

## Executive Summary

| Resource | Count | Status |
|----------|-------|--------|
| EC2 Instances | 5 | 4 running, 1 stopped |
| S3 Buckets | 17 | Active |
| RDS Databases | 1 | Available |
| CloudFront Distributions | 3 | 2 enabled, 1 disabled |
| VPCs | 1 | Active |
| Lambda Functions | 0 | - |
| ECS Clusters | 0 | - |
| DynamoDB Tables | 0 | - |
| ElastiCache Clusters | 0 | - |
| Elastic Beanstalk Environments | 0 | - |
| Route53 Hosted Zones | 0 | - |

---

## EC2 Instances

### Running Instances

| Name | Instance ID | Type | Public IP | Private IP | Platform |
|------|-------------|------|-----------|------------|----------|
| LIN-PROD - AWS Snapshot Server | i-e9cfab05 | t2.micro | 107.22.137.38 | 172.30.0.113 | Linux |
| LIN-PROD - Metabase | i-0e71258ae855b2904 | t2.micro | 23.20.101.74 | 172.30.0.153 | Linux |
| WIN-PROD - Main Server 2019 | i-06f495c680babfec6 | m5a.large | 23.23.188.123 | 172.30.0.91 | Windows |
| WIN-PROD - PlacementSpider | i-011f988bc2319bbcf | t2.medium | 54.89.152.118 | 172.30.0.251 | Windows |

### Stopped Instances

| Name | Instance ID | Type | Private IP | Platform |
|------|-------------|------|------------|----------|
| OpenVPN Server | i-00825d0e8add73516 | t2.micro | 172.30.2.122 | Linux |

### Instance Details

#### LIN-PROD - AWS Snapshot Server
- **Instance ID:** i-e9cfab05
- **Launch Date:** 2014-12-15 (relaunched 2016-09-10)
- **Key Pair:** Brandpoint
- **Security Group:** SSH-Only (sg-d19162b5)
- **Availability Zone:** us-east-1a

#### LIN-PROD - Metabase
- **Instance ID:** i-0e71258ae855b2904
- **Launch Date:** 2018-08-10 (relaunched 2022-02-09)
- **Key Pair:** adfusion
- **Security Group:** MetaBase Security (sg-07da609aa77b467c9)
- **Availability Zone:** us-east-1a

#### WIN-PROD - Main Server 2019
- **Instance ID:** i-06f495c680babfec6
- **Launch Date:** 2019-09-30
- **Key Pair:** adfusion
- **Security Groups:** WindowsWebServer (sg-2329245f), Brandpoint-WindowsWebServer (sg-04e036eec890d2b9a)
- **Availability Zone:** us-east-1a
- **EBS Optimized:** Yes
- **Additional Storage:** xvdf volume attached

#### WIN-PROD - PlacementSpider
- **Instance ID:** i-011f988bc2319bbcf
- **Launch Date:** 2020-07-29
- **Key Pair:** adfusion
- **Security Group:** Brandpoint-WindowsWebServer (sg-04e036eec890d2b9a)
- **Availability Zone:** us-east-1a

#### OpenVPN Server (STOPPED)
- **Instance ID:** i-00825d0e8add73516
- **Launch Date:** 2025-12-10
- **Key Pair:** adfusion
- **Security Group:** VpnServerSecurityGroup (sg-01e2e6dbde36652f4)
- **Availability Zone:** us-east-1c
- **Stopped:** 2026-01-02 (User initiated shutdown)

---

## VPC Configuration

### VPC: vpc-d26af3b7 (Default)
- **CIDR Block:** 172.30.0.0/16
- **Tenancy:** default
- **DHCP Options:** dopt-39160c5b

### Subnets
| Subnet ID | Availability Zone | Notes |
|-----------|-------------------|-------|
| subnet-3d49ed64 | us-east-1a | Most instances |
| subnet-4eb4d974 | us-east-1c | OpenVPN Server |
| subnet-aa43c6dd | us-east-1d | - |
| subnet-f91bdad2 | us-east-1e | - |

---

## S3 Buckets

| Bucket Name | Created | Purpose |
|-------------|---------|---------|
| HouseTopia | 2014-07-21 | Legacy |
| aracontent | 2010-02-22 | Content storage |
| brandpoint-admin-assets | 2019-04-17 | Admin assets |
| brandpoint-ai-dev-lambda-code-144105412483 | 2026-01-20 | AI Lambda code |
| brandpoint-ai-dev-model-artifacts-144105412483 | 2026-01-21 | AI model artifacts |
| brandpoint-ai-dev-templates-144105412483 | 2026-01-21 | AI templates |
| brandpoint-corp-backup | 2025-09-16 | Corporate backup |
| brandpoint-hub-assets | 2015-05-27 | Hub assets |
| brandpoint-hub-files | 2017-08-15 | Hub files |
| brandpoint-images | 2014-04-09 | Image storage |
| brandpoint-pubdocs | 2013-04-04 | Public documents |
| brandpoint-restic | 2021-11-17 | Restic backups |
| brandpoint-wpvivid | 2021-01-15 | WordPress backups |
| brandpoint-xdata-backup | 2022-10-13 | XData backup |
| elasticbeanstalk-us-east-1-144105412483 | 2017-02-10 | Elastic Beanstalk |
| images.brandpointcontent | 2014-05-02 | Content images |
| infographics.brandpointcontent | 2014-06-04 | Infographics |

---

## RDS Database

### brandpointdb
| Property | Value |
|----------|-------|
| **Engine** | SQL Server SE 15.00.4198.2 |
| **Instance Class** | db.m5.xlarge |
| **Storage** | 300 GB (gp2) |
| **Endpoint** | brandpointdb.c5rp85tg25on.us-east-1.rds.amazonaws.com:1433 |
| **Master Username** | BpUser |
| **Multi-AZ** | No |
| **Publicly Accessible** | Yes |
| **Storage Encrypted** | No |
| **Deletion Protection** | Yes |
| **Backup Retention** | 5 days |
| **Backup Window** | 04:13-04:43 UTC |
| **Maintenance Window** | Tue 03:13-03:43 UTC |
| **Availability Zone** | us-east-1a |
| **VPC Security Group** | sg-5f91623b |

---

## CloudFront Distributions

### 1. E3U3RN3OBEX6IT (DISABLED)
- **Domain:** d27jyyjnsasovi.cloudfront.net
- **Aliases:** media.adfusion.com, cdn.adfusion.com
- **Origin:** adfusion.s3.amazonaws.com
- **Status:** Disabled

### 2. E174DL9C8B9SVK (ENABLED)
- **Domain:** d26v8lyymp918m.cloudfront.net
- **Aliases:** cdn.aracontent.com, cdn.brandpoint.com
- **Origin:** aracontent.s3.amazonaws.com
- **Status:** Enabled

### 3. E1YIG7FY83LJ1Q (ENABLED)
- **Domain:** d372qxeqh8y72i.cloudfront.net
- **Aliases:** None
- **Origin:** images.brandpointcontent.s3.amazonaws.com
- **Status:** Enabled

---

## IAM Roles (23 total)

### Custom Roles
| Role Name | Purpose |
|-----------|---------|
| aws-elasticbeanstalk-ec2-role | Elastic Beanstalk EC2 |
| aws-elasticbeanstalk-service-role | Elastic Beanstalk service |
| EMR_AutoScaling_DefaultRole | EMR auto-scaling |
| EMR_DefaultRole | EMR default |
| EMR_EC2_DefaultRole | EMR EC2 |
| Engagement-Tracker-With-Cube-Js-role-ktwgi9nh | Lambda (Engagement Tracker) |
| event-analytics-backend-dev-us-east-1-lambdaRole | Lambda (Event Analytics) |
| serverlessApiGatewayCloudWatchRole | API Gateway CloudWatch |

### Service-Linked Roles
- AWSServiceRoleForAmazonEventBridgeApiDestinations
- AWSServiceRoleForAmazonOpenSearchService
- AWSServiceRoleForAPIGateway
- AWSServiceRoleForAutoScaling
- AWSServiceRoleForElastiCache
- AWSServiceRoleForElasticBeanstalk
- AWSServiceRoleForElasticLoadBalancing
- AWSServiceRoleForEMRCleanup
- AWSServiceRoleForRDS
- AWSServiceRoleForResourceExplorer
- AWSServiceRoleForSupport
- AWSServiceRoleForTrustedAdvisor
- AWSDataLifecycleManagerDefaultRole

---

## Key Pairs in Use

| Key Name | Used By |
|----------|---------|
| Brandpoint | LIN-PROD - AWS Snapshot Server |
| adfusion | All other instances |

---

## Security Groups Overview

| Group Name | Group ID | Description |
|------------|----------|-------------|
| SSH-Only | sg-d19162b5 | SSH from Brandpoint IPs |
| MetaBase Security | sg-07da609aa77b467c9 | Metabase access |
| WindowsWebServer | sg-2329245f | Windows web server |
| Brandpoint-WindowsWebServer | sg-04e036eec890d2b9a | Brandpoint Windows |
| VpnServerSecurityGroup | sg-01e2e6dbde36652f4 | VPN server |
| SQLServer | sg-5f91623b | RDS SQL Server |

---

## Access Notes

### Permissions Verified
- EC2: Full read access
- S3: List buckets
- RDS: Describe instances
- CloudFront: List distributions
- IAM: List roles (but NOT list users)
- VPC: Describe VPCs

### Access Denied
- IAM: ListUsers

---

## Next Steps / Recommendations

1. **Security Review:** RDS is publicly accessible with no storage encryption
2. **Cost Review:** OpenVPN server is stopped - confirm if needed
3. **Backup Verification:** Multiple backup buckets exist - verify backup schedules
4. **CloudFront:** E3U3RN3OBEX6IT is disabled - confirm if intentional

---

*Report generated via AWS CLI reconnaissance - read-only operations only*
