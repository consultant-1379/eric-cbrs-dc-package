#!/usr/bin/env python3

"""
Script to automate the CBRS DC SA enrollment procedure.

The script takes 2 inputs: the entity info id, and the pkiraserv virtual service IP address.
The script is to be run on the General Scripting VM of the ENM to be enrolled with.

The script creates the necessary profiles and entities on the ENM and the output of the script
is the enrollment JSON file that is required to generate the secret.
The JSON is printed at the end of the script output.

The usage of the script is as follows:
    python3 enroll.py <entity_info_id> <pkiraserv_virtual_service_ip>

Example:
    python3 enroll.py ENM_ATH_23-05 10.232.219.85
"""

import argparse
import json
import os
import sys

import enmscripting


def main():
    """
    Script to automate the CBRS DC SA enrollment procedure.
    """
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument(
        "entity_info_id", help="The identifier for the entity to enroll"
    )
    parser.add_argument(
        "pkiraserv_virtual_service_ip",
        help="The IP address of the pkiraserv virtual service",
    )
    args = parser.parse_args()

    work_dir = "enroll_" + args.entity_info_id
    os.mkdir(work_dir)
    os.chdir(work_dir)

    enroll(args.entity_info_id, args.pkiraserv_virtual_service_ip)

def enroll(entity_info_id: str, pkiraserv_virtual_service_ip: str) -> str:
    """
    Returns the JSON content to enroll with the specified entity_info_id and pkiraserv_virtual_service_ip.

    Args:
        entity_info_id: The identifier for the entity to enroll.
        pkiraserv_virtual_service_ip: The IP address of the pkiraserv virtual service.
    """

    print(
        f"Using entity info ID: {entity_info_id} and pkiraserv virtual service IP address: {pkiraserv_virtual_service_ip}"
    )

    session = enmscripting.open()
    cmd = session.command()

    cbrs_dcsa_entity_info_name = f"CBRS_DC_SA_{entity_info_id}-oam"
    cbrs_monitor_entity_info_name = f"CBRS_Monitor_{entity_info_id}-oam"
    cbrs_ext_ldap_entity_info_name = f"CBRS_EXT_LDAP_{entity_info_id}-oam"
    entity_info_otp = "CbrsTestPassw0rd"

    check_https_sbi_ep_profile_exists(cmd)
    check_sbi_com_tpfc_ep_profile_exists(cmd)

    create_trust_profile(cmd)
    create_entity_profile(cmd)

    create_cbrs_dcsa_end_entity(cmd, cbrs_dcsa_entity_info_name, entity_info_otp)
    create_monitor_end_entity(cmd, cbrs_monitor_entity_info_name, entity_info_otp)
    create_external_ldap_end_entity(
        cmd, cbrs_ext_ldap_entity_info_name, entity_info_otp
    )

    common_name = cbrs_dcsa_entity_info_name
    country_name = "SE"
    organisation = "ERICSSON"
    organisation_unit = "BUCI_DUAC_NAM"

    cbrs_dcsa_end_entity_subject_dn = (
        f"CN={common_name},C={country_name},O={organisation},OU={organisation_unit}"
    )
    cbrs_monitor_end_entity_subject_dn = f"CN={cbrs_monitor_entity_info_name},C={country_name},O={organisation},OU={organisation_unit}"
    cbrs_ext_ldap_end_entity_subject_dn = f"CN={cbrs_ext_ldap_entity_info_name},C={country_name},O={organisation},OU={organisation_unit}"

    ca_subject_dn = get_ca_subject_dn(cmd)
    pem_value = get_root_ca_pem_file(cmd)

    eric_sec_certm_deployment_configuration_file_name = (
        "eric-sec-certm-deployment-configuration.json"
    )

    json_file_content = write_the_configuration_json_file(
        pem_value,
        ca_subject_dn,
        pkiraserv_virtual_service_ip,
        entity_info_otp,
        cbrs_dcsa_end_entity_subject_dn,
        cbrs_monitor_end_entity_subject_dn,
        cbrs_ext_ldap_end_entity_subject_dn,
        eric_sec_certm_deployment_configuration_file_name,
    )

    print("\n")
    print("*********************************************************************")
    print("                  Generated JSON enrollment file:                    ")
    print("*********************************************************************\n")
    print(json_file_content)
    print("\n")
    print(
        f"Output JSON enrollment file: {os.getcwd()}/{eric_sec_certm_deployment_configuration_file_name}\n"
    )

    enmscripting.close(session)


def check_https_sbi_ep_profile_exists(cmd):
    """
    Check if the required profile ENM_System_HTTPS_SBI_EP is present in ENM PKI system.

    Args:
        cmd: The ENM scripting command.
    """
    check_https_sbi_ep_profile_exists_command = (
        "pkiadm pfm --list -type entity --name ENM_System_HTTPS_SBI_EP"
    )
    execute_command_and_check_repsonse(
        cmd,
        check_https_sbi_ep_profile_exists_command,
        "ENM_System_HTTPS_SBI_EP, ENTITY_PROFILE",
    )


def check_sbi_com_tpfc_ep_profile_exists(cmd):
    """
    Check if the required profile ENM_System_SBI_COM_TPFC_EP is present in ENM PKI system.

    Args:
        cmd: The ENM scripting command.
    """
    check_sbi_com_tpfc_ep_profile_exists_command = (
        "pkiadm pfm --list -type entity --name ENM_System_SBI_COM_TPFC_EP"
    )
    execute_command_and_check_repsonse(
        cmd,
        check_sbi_com_tpfc_ep_profile_exists_command,
        "ENM_System_SBI_COM_TPFC_EP, ENTITY_PROFILE",
    )


def create_trust_profile(cmd):
    """
    Create CBRS DC SA Trust Profile.

    Args:
        cmd: The ENM scripting command.
    """
    trust_profile = "CBRS_DC_SA_TP"
    trust_profile_file_name = f"{trust_profile}.xml"
    cbrs_dc_sa_tp_file_content = """<?xml version="1.0" encoding="UTF-8"?>
    <Profiles xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="ProfilesSchema.xsd">
      <TrustProfile Name="CBRS_DC_SA_TP">
        <ProfileValidity>2111-03-01</ProfileValidity>
        <Modifiable>true</Modifiable>
        <TrustCAChain>
        <IsChainRequired>true</IsChainRequired>
        <InternalCA>
          <CertificateAuthority>
            <Name>ENM_OAM_CA</Name>
          </CertificateAuthority>
        </InternalCA>
        </TrustCAChain>
      </TrustProfile>
    </Profiles>"""

    create_trust_profile_command = "pkiadm profilemgmt --create --xmlfile file:%s"
    execute_upload_command(
        cmd,
        trust_profile_file_name,
        cbrs_dc_sa_tp_file_content,
        create_trust_profile_command,
        "Profile created Successfully",
    )

    check_trust_profile_created_command = (
        f"pkiadm profilemgmt --view --profiletype trust --name {trust_profile}"
    )
    execute_command_and_check_repsonse(
        cmd, check_trust_profile_created_command, "Is Active: , TRUE"
    )


def create_entity_profile(cmd):
    """
    Create CBRS DC SA Entity Profile.

    Args:
        cmd: The ENM scripting command.
    """
    entity_profile_name = "CBRS_DC_SA_EP"
    entity_profile_file_name = f"{entity_profile_name}.xml"
    cbrs_dc_sa_ep_file_content = """<?xml version="1.0" encoding="UTF-8"?>
    <Profiles xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="ProfilesSchema.xsd">
      <EntityProfile Name="CBRS_DC_SA_EP">
        <ProfileValidity>2111-03-01</ProfileValidity>
        <Modifiable>true</Modifiable>
        <Category>
          <Modifiable>true</Modifiable>
          <Name>node-oam</Name>
        </Category>
        <Subject>
          <SubjectField>
            <Type>COMMON_NAME</Type>
            <Value>?</Value>
          </SubjectField>
          <SubjectField>
            <Type>ORGANIZATION</Type>
            <Value>ERICSSON</Value>
          </SubjectField>
          <SubjectField>
            <Type>COUNTRY_NAME</Type>
            <Value>SE</Value>
          </SubjectField>
          <SubjectField>
            <Type>ORGANIZATION_UNIT</Type>
            <Value>BUCI_DUAC_NAM</Value>
          </SubjectField>
        </Subject>
        <KeyGenerationAlgorithm>
          <Name>RSA</Name>
          <KeySize>2048</KeySize>
        </KeyGenerationAlgorithm>
        <CertificateProfile Name="ENM_System_HTTPS_SBI_CP"/>
        <TrustProfile Name="CBRS_DC_SA_TP"/>
        <KeyUsage>
          <Critical>true</Critical>
          <SupportedKeyUsageType>DIGITAL_SIGNATURE</SupportedKeyUsageType>
          <SupportedKeyUsageType>KEY_ENCIPHERMENT</SupportedKeyUsageType>
          <SupportedKeyUsageType>KEY_AGREEMENT</SupportedKeyUsageType>
        </KeyUsage>
      </EntityProfile>
    </Profiles>"""

    create_entity_profile_command = "pkiadm profilemgmt --create --xmlfile file:%s"
    execute_upload_command(
        cmd,
        entity_profile_file_name,
        cbrs_dc_sa_ep_file_content,
        create_entity_profile_command,
        "Profile created Successfully",
    )

    check_entity_profile_created_command = (
        f"pkiadm profilemgmt --view --profiletype entity --name {entity_profile_name}"
    )
    execute_command_and_check_repsonse(
        cmd, check_entity_profile_created_command, "Is Active: , TRUE"
    )


def create_cbrs_dcsa_end_entity(cmd, cbrs_dcsa_entity_info_name, entity_info_otp):
    """
    End Entity creation for CBRS DC SA instance.

    Args:
        cmd: The ENM scripting command.
        cbrs_dcsa_entity_info_name: entity name
        entity_info_otp: entity one-time password
    """
    end_entity_file_name = f"EE_{cbrs_dcsa_entity_info_name}.xml"
    end_entity_file_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Entities xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="EntitiesSchema.xsd">
      <Entity>
        <PublishCertificatetoTDPS>true</PublishCertificatetoTDPS>
        <EntityProfile Name="CBRS_DC_SA_EP"/>
        <KeyGenerationAlgorithm>
          <Name>RSA</Name>
          <KeySize>2048</KeySize>
        </KeyGenerationAlgorithm>
        <Category>
          <Modifiable>true</Modifiable>
          <Name>NODE-OAM</Name>
        </Category>
        <EntityInfo>
          <Name>{cbrs_dcsa_entity_info_name}</Name>
          <Subject>
            <SubjectField>
              <Type>ORGANIZATION</Type>
              <Value>ERICSSON</Value>
            </SubjectField>
            <SubjectField>
              <Type>ORGANIZATION_UNIT</Type>
              <Value>BUCI_DUAC_NAM</Value>
            </SubjectField>
            <SubjectField>
              <Type>COUNTRY_NAME</Type>
              <Value>SE</Value>
            </SubjectField>
            <SubjectField>
              <Type>COMMON_NAME</Type>
              <Value>{cbrs_dcsa_entity_info_name}</Value>
            </SubjectField>
          </Subject>
          <OTP>{entity_info_otp}</OTP>
          <OTPCount>5</OTPCount>
          <Issuer>
            <Name>ENM_OAM_CA</Name>
          </Issuer>
        </EntityInfo>
        <OTPValidityPeriod>1440</OTPValidityPeriod>
      </Entity>
    </Entities>"""
    create_end_entity_command = "pkiadm etm -c -xf file:%s"

    execute_upload_command(
        cmd,
        end_entity_file_name,
        end_entity_file_content,
        create_end_entity_command,
        "Creation of entity successful",
    )

    check_end_entity_created_command = (
        f"pkiadm etm -l -type ee --name {cbrs_dcsa_entity_info_name}"
    )
    execute_command_and_check_repsonse(
        cmd,
        check_end_entity_created_command,
        cbrs_dcsa_entity_info_name + ", ENTITY, NEW",
    )


def create_monitor_end_entity(cmd, cbrs_monitor_entity_info_name, entity_info_otp):
    """
    End Entity creation for CBRS Monitor.

    Args:
        cmd: The ENM scripting command.
        cbrs_monitor_entity_info_name: entity name
        entity_info_otp: entity one-time password
    """
    monitor_entity_file_name = f"EE_{cbrs_monitor_entity_info_name}.xml"
    cbrs_monitor_entity_file_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Entities xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="EntitiesSchema.xsd">
      <Entity>
        <PublishCertificatetoTDPS>true</PublishCertificatetoTDPS>
        <EntityProfile Name="CBRS_DC_SA_EP"/>
        <KeyGenerationAlgorithm>
          <Name>RSA</Name>
          <KeySize>2048</KeySize>
        </KeyGenerationAlgorithm>
        <Category>
          <Modifiable>true</Modifiable>
          <Name>NODE-OAM</Name>
        </Category>
        <EntityInfo>
        <Name>{cbrs_monitor_entity_info_name}</Name>
          <Subject>
            <SubjectField>
              <Type>ORGANIZATION</Type>
              <Value>ERICSSON</Value>
            </SubjectField>
            <SubjectField>
              <Type>ORGANIZATION_UNIT</Type>
              <Value>BUCI_DUAC_NAM</Value>
            </SubjectField>
            <SubjectField>
              <Type>COUNTRY_NAME</Type>
              <Value>SE</Value>
            </SubjectField>
            <SubjectField>
              <Type>COMMON_NAME</Type>
              <Value>{cbrs_monitor_entity_info_name}</Value>
            </SubjectField>
          </Subject>
          <OTP>{entity_info_otp}</OTP>
          <OTPCount>5</OTPCount>
          <Issuer>
            <Name>ENM_OAM_CA</Name>
          </Issuer>
        </EntityInfo>
        <OTPValidityPeriod>1440</OTPValidityPeriod>
      </Entity>
    </Entities>"""
    create_cbrs_monitor_entity_command = "pkiadm etm -c -xf file:%s"

    execute_upload_command(
        cmd,
        monitor_entity_file_name,
        cbrs_monitor_entity_file_content,
        create_cbrs_monitor_entity_command,
        "Creation of entity successful",
    )

    check_cbrs_monitor_entity_created_command = (
        f"pkiadm etm -l -type ee --name {cbrs_monitor_entity_info_name}"
    )
    execute_command_and_check_repsonse(
        cmd,
        check_cbrs_monitor_entity_created_command,
        cbrs_monitor_entity_info_name + ", ENTITY, NEW",
    )


def create_external_ldap_end_entity(
    cmd, cbrs_ext_ldap_entity_info_name, entity_info_otp
):
    """
    End Entity creation for ENM LDAP as External LDAP.

    Args:
        cmd: The ENM scripting command.
        cbrs_ext_ldap_entity_info_name: entity name
        entity_info_otp: entity one-time password
    """
    ldap_entity_file_name = f"EE_{cbrs_ext_ldap_entity_info_name}.xml"
    ldap_entity_file_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Entities xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="EntitiesSchema.xsd">
      <Entity>
        <PublishCertificatetoTDPS>true</PublishCertificatetoTDPS>
        <EntityProfile Name="CBRS_DC_SA_EP"/>
        <KeyGenerationAlgorithm>
          <Name>RSA</Name>
          <KeySize>2048</KeySize>
        </KeyGenerationAlgorithm>
        <Category>
          <Modifiable>true</Modifiable>
          <Name>NODE-OAM</Name>
        </Category>
        <EntityInfo>
          <Name>{cbrs_ext_ldap_entity_info_name}</Name>
          <Subject>
            <SubjectField>
              <Type>ORGANIZATION</Type>
              <Value>ERICSSON</Value>
            </SubjectField>
            <SubjectField>
              <Type>ORGANIZATION_UNIT</Type>
              <Value>BUCI_DUAC_NAM</Value>
            </SubjectField>
            <SubjectField>
              <Type>COUNTRY_NAME</Type>
              <Value>SE</Value>
            </SubjectField>
            <SubjectField>
              <Type>COMMON_NAME</Type>
              <Value>{cbrs_ext_ldap_entity_info_name}</Value>
            </SubjectField>
          </Subject>
          <OTP>{entity_info_otp}</OTP>
          <OTPCount>5</OTPCount>
          <Issuer>
            <Name>ENM_OAM_CA</Name>
          </Issuer>
          </EntityInfo>
        <OTPValidityPeriod>1440</OTPValidityPeriod>
      </Entity>
    </Entities>"""
    create_ldap_entity_command = "pkiadm entitymgmt --create --xmlfile file:%s"

    execute_upload_command(
        cmd,
        ldap_entity_file_name,
        ldap_entity_file_content,
        create_ldap_entity_command,
        "Creation of entity successful",
    )

    check_ldap_entity_created_command = f"pkiadm entitymgmt --list --entitytype ee --name {cbrs_ext_ldap_entity_info_name}"
    execute_command_and_check_repsonse(
        cmd,
        check_ldap_entity_created_command,
        cbrs_ext_ldap_entity_info_name + ", ENTITY, NEW",
    )


def get_ca_subject_dn(cmd):
    """
    Retrieve the subjectDN of ENM_OAM_CA.
    Args:
        cmd: The ENM scripting command.
    """
    command = "pkiadm ctm CACert -l -en ENM_OAM_CA"
    response = cmd.execute(command)

    print("\nca_subject_dn is: " + response.get_output().groups()[0][0][1].value())
    return response.get_output().groups()[0][0][1].value()


def get_root_ca_pem_file(cmd):
    """
    Get Root CA PEM.

    Args:
        cmd: The ENM scripting command.
    """
    download_root_ca_pem_file_command = (
        "pkiadm certmgmt CACert --exportcert --entityname ENM_PKI_Root_CA --format PEM"
    )
    execute_download_command(cmd, download_root_ca_pem_file_command)
    pem_value = get_pem_value_from_root_ca_file()
    print("\nformatted pem value: " + pem_value)
    return pem_value


def execute_command_and_check_repsonse(cmd, command, expected_in_response):
    print("************ Executing command and checking response ************ ")
    print("\nExecuting command: " + command)
    response = cmd.execute(command)
    print("\nCommand response: " + str(response.get_output()))
    check_response(response, expected_in_response)


def execute_upload_command(
    cmd, file_to_upload, file_content, command, expected_in_response
):
    print("************ Executing upload command and checking response ************ ")
    print("\nfile name to upload: " + file_to_upload)
    print("\nfile content: " + file_content)
    with open(file_to_upload, "wb") as file_upload:
        file_upload.write(file_content.encode())

    command_to_run = command % (os.path.basename(file_to_upload))
    with open(file_to_upload, "rb") as file_upload:
        response = cmd.execute(command_to_run, file_upload)
        print("Upload Command response: " + str(response.get_output()))

    check_response(response, expected_in_response)


def execute_download_command(cmd, command):
    print("************ Executing download command and checking response ************ ")
    print("\nExecuting download command: " + command)
    result = cmd.execute(command)
    print("\nDownload command response: " + str(result.get_output()))
    if result.has_files():
        for enm_file in result.files():
            enm_file.download()
    else:
        print("\nFailure for " + command + "\n")


def get_pem_value_from_root_ca_file():
    """
    Reads the contents of the Root CA PEM file.
    """
    with open("ENM_PKI_Root_CA.pem", "r") as root_ca_file:
        stripped_pem = root_ca_file.read().replace("\n", "")
        formatted_pem_value = stripped_pem.replace(
            "-----BEGIN CERTIFICATE-----", "-----BEGIN CERTIFICATE-----\\n"
        ).replace("-----END CERTIFICATE-----", "\\n-----END CERTIFICATE-----")

        return formatted_pem_value


def write_the_configuration_json_file(
    pem_value,
    ca_subject_dn,
    pkiraserv_virtual_service_ip,
    entity_info_otp,
    cbrs_dcsa_end_entity_subject_dn,
    cbrs_monitor_end_entity_subject_dn,
    cbrs_ext_ldap_end_entity_subject_dn,
    eric_sec_certm_deployment_configuration_file_name,
):
    eric_sec_certm_deployment_configuration_file_content = f"""
    {{
        "ca-certs": [
            {{
                "name": "cbrsDcSaEnmCaCerts",
                "pem": "{pem_value}"
            }}
        ],
        "certificate-authorities": {{
            "certificate-authority": [
                {{
                    "name": "CN=ENM_OAM_CA"
                }}
            ]
        }},
        "cmp-server-groups": {{
            "cmp-server-group": [
                {{
                    "name": "cmpGroupCbrsDcSaEnm",
                    "cmp-server": [
                        {{
                            "name": "cmpServerCbrsDcSaEnm",
                            "ca-certs": "cbrsDcSaEnmCaCerts",
                            "uri": "http://{pkiraserv_virtual_service_ip}:8091/pkira-cmp/synch",
                            "certificate-authority": "{ca_subject_dn}",
                            "priority": 1,
                            "ra-mode-enabled": false
                        }}
                    ]
                }}
            ]
        }},
        "enrollments": [
            {{
                "name": "cbrs-dc-sa-enm",
                "certificate-name": "cbrs-dc-sa-enm",
                "algorithm": "rsa2048",
                "cmp-server-group": "cmpGroupCbrsDcSaEnm",
                "subject": "{cbrs_dcsa_end_entity_subject_dn}",
                "subject-alternative-names": ["DNS:eric-cbrs-dc-sa-hostname.com"],
                "password": "{entity_info_otp}",
                "trusted-certs": "cbrsPubsDcSaEnmCaCerts"
            }},
            {{
                "name": "cbrs-monitor-enm",
                "certificate-name": "cbrs-monitor-enm",
                "algorithm": "rsa2048",
                "cmp-server-group": "cmpGroupCbrsDcSaEnm",
                "subject": "{cbrs_monitor_end_entity_subject_dn}",
                "subject-alternative-names": ["DNS:eric-cbrs-monitor-hostname.com"],
                "password": "{entity_info_otp}",
                "trusted-certs": "cbrsPubsDcSaEnmCaCerts"
            }},
            {{
                "name": "iam-authentication-ldap-client",
                "certificate-name": "iam-authentication-ldap-client",
                "algorithm": "rsa2048",
                "cmp-server-group": "cmpGroupCbrsDcSaEnm",
                "subject": "{cbrs_ext_ldap_end_entity_subject_dn}",
                "subject-alternative-names": ["DNS:eric-cbrs-ext-ldap-hostname.com"],
                "password": "{entity_info_otp}",
                "trusted-certs": "iam-authentication-ldap-client"
            }}
        ],
        "enrollment-retry-timeout": 60
    }}
    """
    with open(eric_sec_certm_deployment_configuration_file_name, "w") as certm_file:
        json.dump(
            json.loads(eric_sec_certm_deployment_configuration_file_content),
            certm_file,
            indent=2,
        )
    return eric_sec_certm_deployment_configuration_file_content


def check_response(response, expected_in_response):
    result_string = str(response.get_output())
    if (
        expected_in_response in result_string
        or "Profile already exists" in result_string
        or "Entity already exists" in result_string
    ):
        print("Command successfully executed\n")
    else:
        raise ValueError(
            f"Expected: {expected_in_response} not contained in the response: {response.get_output()}"
        )


if __name__ == "__main__":
    main()
