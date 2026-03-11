
meta
  version s = 1.2.0
  lastUpdated s = 2026-03-07
  organization s = Integration COE
  catalogOwner s = Integration COE Lead

layerSuggestions
  0 s = EAPI
  1 s = PAPI
  2 s = SAPI
  3 s = BATCH
  4 s = EVENT
  5 s = UTILITY
  6 s = FACADE

contractTypes
  0 s = REST
  1 s = SOAP
  2 s = Kafka
  3 s = AsyncAPI
  4 s = GraphQL
  5 s = SFTP
  6 s = JMS
  7 s = Other

tribes[]
  id s = tribe-cx
  name s = Customer Experience
  lead s = tribe.lead@example.com

businessCapabilities[]
  l0 s = Customer Management
  l1 s = Customer Profile
  l2 s = Identity & Auth

apis[]
  id s = api-001
  name s = Customer Profile API
  repoApiName s = customer-profile-api
  version s = 2.3.1
  layer s = EAPI
  protocol s = REST
  runtime s = MuleSoft 4.3
  javaVersion s = Java 8
  deploymentModel s = OnPrem
  environments
    0 s = DEV
    1 s = SIT
    2 s = UAT
    3 s = PROD
  tribeId s = tribe-cx
  owningSquad s = Squad Alpha
  applicationContext s = CRM Portal
  ramlSpec s = https://anypoint.example.com/api/customer-profile
  businessCapability
    l0 s = Customer Management
    l1 s = Customer Profile
    l2 s = Identity & Auth
  consumers[]
    system s = UXP Portal
    environments
      0 s = UAT
      1 s = PROD
    contractType s = REST
    notes s = Primary consumer — renders customer header
  upstreamSystems[]
    system s = Salesforce CRM
    environments
      0 s = PROD
    protocol s = REST
    notes s = Source of truth for customer master data
  status s = Active
  migrationStatus s = Not Started
  migrationComplexity s = Medium
  confluenceLinks[]
    label s = LLD
    url s = https://confluence.example.com/display/api-001
  designReferences[]
    label s = Sequence Diagram
    url s = https://confluence.example.com/display/api-001-seq
  operationalNotes
    0 s = Free text operational note
  tags
    0 s = customer
    1 s = identity
    2 s = core
  lastReviewedBy s = john.doe@example.com
  lastReviewedDate s = 2026-03-07
  security
    authScheme s = OAuth 2.0 (Client Credentials)
    oauthScopes
      0 s = profile:read
      1 s = profile:write
    tlsVersion s = TLS 1.2
    gatewayPolicies
      0 s = Rate Limiting
      1 s = JWT Validation
      2 s = IP Allowlist
    dataClassification s = Confidential
    complianceFlags
      0 s = GDPR
    secretsVaultPath s = /secret/prod/customer-profile
    certExpiry s = 2026-09-01
    knownVulnerabilities
      0 s = Free text security finding
  solutionDesign
    architecturalPattern s = Facade — aggregates CRM + Identity
    versioningStrategy s = URI versioning (/v2/)
    errorHandlingStrategy s = Standard error envelope with correlation-id
    slaTarget s = 99.9% / < 500ms P95
    asyncApiSpec s = https://asyncapi.example.com/api-001
    adrLinks[]
      label s = ADR-001 Auth Strategy
      url s = https://confluence.example.com/adr-001
    technicalDebt
      0 s = No pagination on /customers/search
    domainEvents
      0 s = customer.updated
      1 s = customer.deleted
  operations
    oncallContact s = squad-alpha@example.com
    monitoringLinks[]
      label s = Datadog Dashboard
      url s = https://app.datadoghq.com/dashboard/abc
    alertingThreshold s = Error rate > 2% over 5 min triggers P2
    maintenanceWindow s = Sundays 02:00-04:00 UTC
    runbookLinks[]
      label s = Timeout Runbook
      url s = https://confluence.example.com/runbook-001
    incidentRefs
      0 s = INC-20241103 — description of incident
    knownFragilities
      0 s = SAP BAPI single point of failure — no circuit breaker
    pipelineLink s = https://jenkins.example.com/job/customer-profile-api
    uptimeSla s = 99.9%