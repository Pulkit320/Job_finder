import hashlib
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class WorkType(str, Enum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ONSITE = "Onsite"
    UNKNOWN = "Unknown"

class LegitimacyType(str, Enum):
    OFFICIAL_CAREERS = "Official Company Careers"
    MAJOR_JOB_BOARD = "Major Job Board"
    THIRD_PARTY_AGGREGATOR = "Third-party Aggregator"
    SUSPICIOUS = "Suspicious"

class VerificationStatus(str, Enum):
    VERIFIED = "Verified"
    UNVERIFIED = "Unverified"
    FAILED = "Failed"

class Job(BaseModel):
    id: str = ""
    title: str = Field(..., alias="Job Title")
    company: str = Field(..., alias="Company")
    posting_date: str = Field(default="", alias="Posting Date")
    application_deadline: str = Field(default="Not specified", alias="Application Deadline")
    location: str = Field(default="Not specified", alias="Location")
    work_type: str = Field(default=WorkType.UNKNOWN.value, alias="Remote / Hybrid / Onsite")
    experience: str = Field(default="Not specified", alias="Experience")
    employment_type: str = Field(default="Full-time", alias="Employment Type")
    salary: str = Field(default="Not specified", alias="Salary")
    application_url: str = Field(..., alias="Application Link")
    company_career_url: str = Field(default="", alias="Company Career Link")
    source: str = Field(default="Unknown", alias="Source")
    legitimacy: str = Field(default=LegitimacyType.THIRD_PARTY_AGGREGATOR.value, alias="Legitimacy")
    verification_status: str = Field(default=VerificationStatus.UNVERIFIED.value, alias="Verification Status")
    description: str = Field(default="", alias="Description")
    date_discovered: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"), alias="Date Discovered")

    class Config:
        populate_by_name = True
        use_enum_values = True

    def model_post_init(self, __context):
        if not self.id:
            raw = f"{self.company.lower().strip()}_{self.title.lower().strip()}_{self.application_url.strip()}"
            self.id = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        if not self.posting_date:
            self.posting_date = datetime.now().strftime("%Y-%m-%d")
        if not self.company_career_url and self.application_url:
            self.company_career_url = self.application_url

    def to_csv_dict(self) -> dict:
        return {
            "Job Title": self.title,
            "Company": self.company,
            "Posting Date": self.posting_date,
            "Application Deadline": self.application_deadline,
            "Location": self.location,
            "Remote / Hybrid / Onsite": self.work_type,
            "Experience": self.experience,
            "Employment Type": self.employment_type,
            "Salary": self.salary,
            "Application Link": self.application_url,
            "Company Career Link": self.company_career_url,
            "Source": self.source,
            "Legitimacy": self.legitimacy,
            "Verification Status": self.verification_status,
            "Description": self.description[:500] + "..." if len(self.description) > 500 else self.description,
            "Date Discovered": self.date_discovered,
        }
