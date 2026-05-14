from __future__ import annotations

import argparse
import csv
import random
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from faker import Faker


COLUMNS = [
	"PGAMpnId",
	"TrainingActivityId",
	"TrainingTitle",
	"TrainingType",
	"IndividualFirstName",
	"IndividualLastName",
	"Email",
	"CorpEmail",
	"TrainingCompletionDate",
	"ExpirationDate",
	"ActivationStatus",
	"Month",
	"MPNId",
	"PartnerName",
	"PartnerCityLocation",
	"PartnerCountryLocation",
	"AADUserId",
	"UserCount",
]

PGAMPN_ID = 1234567
PARTNER_NAME = "Contoso"
PARTNER_CITY = "Reading"
PARTNER_COUNTRY = "UnitedKingdom"
USER_COUNT = 1
DEFAULT_OUTPUT = "SampleTrainings.csv"
DEFAULT_ROW_COUNT = 42_102
DEFAULT_FULL_TARGET_LEARNERS = 5
DEFAULT_TWO_TARGET_LEARNERS = 103
DEFAULT_ONE_TARGET_LEARNERS = 1071
TODAY = date.today()
MIN_EXPIRATION_OFFSET = timedelta(days=28)

TARGET_CERT_TITLES = [
	"Microsoft Certified: Azure AI Engineer Associate",
	"GitHub Copilot",
	"Microsoft Certified: Agentic AI Business Solutions Architect",
]


@dataclass(frozen=True)
class Activity:
	activity_id: str
	title: str
	training_type: str
	related_exam_id: str | None = None
	expires: bool = True
	target: bool = False


@dataclass
class Learner:
	first_name: str
	last_name: str
	personal_email: str
	corp_email: str
	aad_user_id: str
	used_activity_ids: set[str] = field(default_factory=set)


EXAMS: dict[str, Activity] = {
	"AI-102": Activity("AI-102", "Designing and Implementing a Microsoft Azure AI Solution", "Exam", expires=False),
	"GH-300": Activity("GH-300", "GitHub Copilot", "Exam", expires=False),
	"AI-3018": Activity("AI-3018", "Designing Agentic AI Business Solutions", "Exam", expires=False),
	"AZ-900": Activity("AZ-900", "Microsoft Azure Fundamentals", "Exam", expires=False),
	"AI-900": Activity("AI-900", "Microsoft Azure AI Fundamentals", "Exam", expires=False),
	"DP-900": Activity("DP-900", "Microsoft Azure Data Fundamentals", "Exam", expires=False),
	"PL-900": Activity("PL-900", "Microsoft Power Platform Fundamentals", "Exam", expires=False),
	"SC-900": Activity("SC-900", "Microsoft Security, Compliance, and Identity Fundamentals", "Exam", expires=False),
	"AZ-104": Activity("AZ-104", "Microsoft Azure Administrator", "Exam", expires=False),
	"AZ-204": Activity("AZ-204", "Developing Solutions for Microsoft Azure", "Exam", expires=False),
	"AZ-305": Activity("AZ-305", "Designing Microsoft Azure Infrastructure Solutions", "Exam", expires=False),
	"AZ-400": Activity("AZ-400", "Designing and Implementing Microsoft DevOps Solutions", "Exam", expires=False),
	"AZ-500": Activity("AZ-500", "Microsoft Azure Security Technologies", "Exam", expires=False),
	"DP-100": Activity("DP-100", "Designing and Implementing a Data Science Solution on Azure", "Exam", expires=False),
	"DP-203": Activity("DP-203", "Data Engineering on Microsoft Azure", "Exam", expires=False),
	"DP-600": Activity("DP-600", "Implementing Analytics Solutions Using Microsoft Fabric", "Exam", expires=False),
	"PL-200": Activity("PL-200", "Microsoft Power Platform Functional Consultant", "Exam", expires=False),
	"PL-300": Activity("PL-300", "Microsoft Power BI Data Analyst", "Exam", expires=False),
	"PL-400": Activity("PL-400", "Microsoft Power Platform Developer", "Exam", expires=False),
	"PL-500": Activity("PL-500", "Microsoft Power Automate RPA Developer", "Exam", expires=False),
	"PL-600": Activity("PL-600", "Microsoft Power Platform Solution Architect", "Exam", expires=False),
	"SC-200": Activity("SC-200", "Microsoft Security Operations Analyst", "Exam", expires=False),
	"SC-300": Activity("SC-300", "Microsoft Identity and Access Administrator", "Exam", expires=False),
	"SC-401": Activity("SC-401", "Administering Information Security in Microsoft 365", "Exam", expires=False),
	"MB-210": Activity("MB-210", "Microsoft Dynamics 365 Sales Functional Consultant", "Exam", expires=False),
	"MB-230": Activity("MB-230", "Microsoft Dynamics 365 Customer Service Functional Consultant", "Exam", expires=False),
	"MB-700": Activity("MB-700", "Microsoft Dynamics 365: Finance and Operations Apps Solution Architect", "Exam", expires=False),
	"MB-800": Activity("MB-800", "Microsoft Dynamics 365 Business Central Functional Consultant", "Exam", expires=False),
	"MB-910": Activity("MB-910", "Microsoft Dynamics 365 Fundamentals Customer Engagement Apps", "Exam", expires=False),
	"MS-500": Activity("MS-500", "Microsoft 365 Security Administration", "Exam", expires=False),
	"MS-721": Activity("MS-721", "Collaboration Communications Systems Engineer", "Exam", expires=False),
}

CERTIFICATIONS: dict[str, Activity] = {
	"3086": Activity(
		"3086",
		"Microsoft Certified: Azure AI Engineer Associate",
		"Certification",
		related_exam_id="AI-102",
		target=True,
	),
	"3232": Activity("3232", "GitHub Copilot", "Certification", related_exam_id="GH-300", target=True),
	"3250": Activity(
		"3250",
		"Microsoft Certified: Agentic AI Business Solutions Architect",
		"Certification",
		related_exam_id="AI-3018",
		target=True,
	),
	"3067": Activity("3067", "Microsoft Certified: Azure Fundamentals", "Certification", related_exam_id="AZ-900", expires=False),
	"3146": Activity("3146", "Microsoft Certified: Azure AI Fundamentals", "Certification", related_exam_id="AI-900", expires=False),
	"3145": Activity("3145", "Microsoft Certified: Azure Data Fundamentals", "Certification", related_exam_id="DP-900", expires=False),
	"3132": Activity("3132", "Microsoft Certified: Power Platform Fundamentals", "Certification", related_exam_id="PL-900", expires=False),
	"3182": Activity("3182", "Microsoft Certified: Security, Compliance, and Identity Fundamentals", "Certification", related_exam_id="SC-900", expires=False),
	"3139": Activity("3139", "Microsoft Certified: Azure Administrator Associate", "Certification", related_exam_id="AZ-104"),
	"3140": Activity("3140", "Microsoft Certified: Azure Developer Associate", "Certification", related_exam_id="AZ-204"),
	"3162": Activity("3162", "Microsoft Certified: Azure Solutions Architect Expert", "Certification", related_exam_id="AZ-305"),
	"3082": Activity("3082", "Microsoft Certified: DevOps Engineer Expert", "Certification", related_exam_id="AZ-400"),
	"3091": Activity("3091", "Microsoft Certified: Azure Security Engineer Associate", "Certification", related_exam_id="AZ-500"),
	"3087": Activity("3087", "Microsoft Certified: Azure Data Scientist Associate", "Certification", related_exam_id="DP-100"),
	"3088": Activity("3088", "Microsoft Certified: Azure Data Engineer Associate", "Certification", related_exam_id="DP-203"),
	"3227": Activity("3227", "Microsoft Certified: Fabric Analytics Engineer Associate", "Certification", related_exam_id="DP-600"),
	"3153": Activity("3153", "Microsoft Certified: Power Platform Functional Consultant Associate", "Certification", related_exam_id="PL-200"),
	"3142": Activity("3142", "Microsoft Certified: Power BI Data Analyst Associate", "Certification", related_exam_id="PL-300"),
	"3154": Activity("3154", "Microsoft Certified: Power Platform Developer Associate", "Certification", related_exam_id="PL-400"),
	"3188": Activity("3188", "Microsoft Certified: Power Platform Solution Architect Expert", "Certification", related_exam_id="PL-600"),
	"3231": Activity("3231", "Microsoft Certified: Information Security Administrator Associate", "Certification", related_exam_id="SC-401"),
	"3079": Activity("3079", "Microsoft 365 Certified: Security Administrator Associate", "Certification", related_exam_id="MS-500"),
	"3175": Activity("3175", "Microsoft Certified: Dynamics 365 Fundamentals (CRM)", "Certification", related_exam_id="MB-910", expires=False),
	"3215": Activity("3215", "Microsoft Certified: Dynamics 365 Field Service Functional Consultant Associate", "Certification", related_exam_id="MB-230"),
	"3155": Activity("3155", "Microsoft Certified: Dynamics 365 Business Central Functional Consultant Associate", "Certification", related_exam_id="MB-800"),
	"1519": Activity("1519", "Microsoft Certified Professional", "Certification", expires=False),
}

TARGET_CERTS = [activity for activity in CERTIFICATIONS.values() if activity.target]
NON_TARGET_CERTS = [activity for activity in CERTIFICATIONS.values() if not activity.target]
NON_TARGET_EXAMS = [activity for activity in EXAMS.values() if activity.activity_id not in {"AI-102", "GH-300", "AI-3018"}]


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Generate synthetic Partner Center training activity data.")
	parser.add_argument("--output", default=DEFAULT_OUTPUT, help=f"CSV output path. Defaults to {DEFAULT_OUTPUT}.")
	parser.add_argument("--rows", type=int, default=DEFAULT_ROW_COUNT, help="Number of synthetic rows to generate.")
	parser.add_argument("--seed", type=int, default=20260504, help="Random seed for reproducible output.")
	parser.add_argument("--skip-validation", action="store_true", help="Generate the CSV without notebook-style validation.")
	return parser.parse_args()


def stable_aad_user_id(first_name: str, last_name: str, corp_email: str) -> str:
	identity_key = f"{first_name.strip().lower()}|{last_name.strip().lower()}|{corp_email.strip().lower()}"
	return str(uuid.uuid5(uuid.NAMESPACE_DNS, identity_key))


def email_part(value: str) -> str:
	ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
	cleaned_value = re.sub(r"[^a-z0-9]+", ".", ascii_value.lower()).strip(".")
	return cleaned_value or "learner"


def contoso_email(first_name: str, last_name: str) -> str:
	return f"{email_part(first_name)}.{email_part(last_name)}@contoso.com"


def personal_email(first_name: str, last_name: str) -> str:
	return f"{email_part(first_name)}.{email_part(last_name)}@example.com"


def make_learner(fake: Faker, used_names: set[tuple[str, str]]) -> Learner:
	for _ in range(100):
		first_name = fake.first_name()
		last_name = fake.last_name()
		if (first_name, last_name) not in used_names:
			used_names.add((first_name, last_name))
			break
	else:
		first_name = fake.first_name()
		last_name = f"{fake.last_name()}{len(used_names)}"
		used_names.add((first_name, last_name))

	learner_email = personal_email(first_name, last_name)
	corp_email = contoso_email(first_name, last_name)
	aad_user_id = stable_aad_user_id(first_name, last_name, corp_email)
	return Learner(first_name, last_name, learner_email, corp_email, aad_user_id)


def random_date(random_generator: random.Random, start: date, end: date) -> date:
	day_count = (end - start).days
	return start + timedelta(days=random_generator.randint(0, day_count))


def add_years(source_date: date, years: int) -> date:
	try:
		return source_date.replace(year=source_date.year + years)
	except ValueError:
		return source_date.replace(month=2, day=28, year=source_date.year + years)


def format_completion(completion_date: date) -> str:
	return f"{completion_date.isoformat()}T00:00:00.000Z"


def format_expiration(expiration_date: date | None) -> str:
	if expiration_date is None:
		return ""
	return f"{expiration_date.isoformat()} 00:00:00"


def month_label(completion_date: date) -> str:
	return completion_date.strftime("%b-%Y")


def activation_status(activity: Activity, expiration_date: date | None) -> str:
	if activity.training_type == "Certification" and expiration_date is not None and expiration_date < TODAY:
		return "Expired"
	return "Active"


def build_row(learner: Learner, activity: Activity, completion_date: date, expiration_date: date | None) -> dict[str, object]:
	return {
		"PGAMpnId": PGAMPN_ID,
		"TrainingActivityId": activity.activity_id,
		"TrainingTitle": activity.title,
		"TrainingType": activity.training_type,
		"IndividualFirstName": learner.first_name,
		"IndividualLastName": learner.last_name,
		"Email": learner.personal_email,
		"CorpEmail": learner.corp_email,
		"TrainingCompletionDate": format_completion(completion_date),
		"ExpirationDate": format_expiration(expiration_date),
		"ActivationStatus": activation_status(activity, expiration_date),
		"Month": month_label(completion_date),
		"MPNId": PGAMPN_ID,
		"PartnerName": PARTNER_NAME,
		"PartnerCityLocation": PARTNER_CITY,
		"PartnerCountryLocation": PARTNER_COUNTRY,
		"AADUserId": learner.aad_user_id,
		"UserCount": USER_COUNT,
	}


def add_exam_row(rows: list[dict[str, object]], learner: Learner, exam: Activity, completion_date: date) -> None:
	rows.append(build_row(learner, exam, completion_date, None))
	learner.used_activity_ids.add(exam.activity_id)


def add_certification_row(
	rows: list[dict[str, object]],
	learner: Learner,
	certification: Activity,
	completion_date: date,
	expiration_date: date | None,
) -> None:
	rows.append(build_row(learner, certification, completion_date, expiration_date))
	learner.used_activity_ids.add(certification.activity_id)


def add_certification_bundle(
	rows: list[dict[str, object]],
	learner: Learner,
	certification: Activity,
	random_generator: random.Random,
	completion_date: date | None = None,
	expiration_date: date | None = None,
) -> None:
	if completion_date is None:
		completion_date = random_date(random_generator, date(2019, 1, 1), TODAY)

	if certification.related_exam_id:
		exam = EXAMS[certification.related_exam_id]
		exam_completion = completion_date - timedelta(days=random_generator.randint(7, 90))
		add_exam_row(rows, learner, exam, exam_completion)

	if expiration_date is None and certification.expires:
		expiration_years = random_generator.choice([1, 1, 2, 2, 3])
		expiration_date = add_years(completion_date, expiration_years)

	if expiration_date is not None:
		minimum_expiration = TODAY + MIN_EXPIRATION_OFFSET
		if expiration_date < minimum_expiration:
			expiration_date = minimum_expiration + timedelta(days=random_generator.randint(0, 180))

	add_certification_row(rows, learner, certification, completion_date, expiration_date)


def add_target_certification_bundle(
	rows: list[dict[str, object]], learner: Learner, certification: Activity, random_generator: random.Random
) -> None:
	expiration_date = TODAY + timedelta(days=random_generator.randint(MIN_EXPIRATION_OFFSET.days, 540))
	completion_date = expiration_date - timedelta(days=365)
	add_certification_bundle(rows, learner, certification, random_generator, completion_date, expiration_date)


def add_target_cohorts(
	rows: list[dict[str, object]], fake: Faker, random_generator: random.Random, used_names: set[tuple[str, str]]
) -> None:
	for _ in range(DEFAULT_FULL_TARGET_LEARNERS):
		learner = make_learner(fake, used_names)
		for certification in TARGET_CERTS:
			add_target_certification_bundle(rows, learner, certification, random_generator)

	for learner_index in range(DEFAULT_TWO_TARGET_LEARNERS):
		learner = make_learner(fake, used_names)
		missing_index = learner_index % len(TARGET_CERTS)
		for certification_index, certification in enumerate(TARGET_CERTS):
			if certification_index != missing_index:
				add_target_certification_bundle(rows, learner, certification, random_generator)

	for learner_index in range(DEFAULT_ONE_TARGET_LEARNERS):
		learner = make_learner(fake, used_names)
		cert_index = learner_index % len(TARGET_CERTS)
		certification = TARGET_CERTS[cert_index]
		add_target_certification_bundle(rows, learner, certification, random_generator)


def unused_activity(learner: Learner, activities: list[Activity], random_generator: random.Random) -> Activity:
	available_activities = [activity for activity in activities if activity.activity_id not in learner.used_activity_ids]
	if not available_activities:
		available_activities = activities
	return random_generator.choice(available_activities)


def add_non_target_rows(
	rows: list[dict[str, object]],
	fake: Faker,
	random_generator: random.Random,
	used_names: set[tuple[str, str]],
	total_rows: int,
) -> None:
	while len(rows) < total_rows:
		learner = make_learner(fake, used_names)
		planned_rows = random_generator.choices(
			population=[1, 2, 3, 4, 5, 6, 7, 8],
			weights=[10, 14, 18, 20, 18, 12, 6, 2],
			k=1,
		)[0]

		while planned_rows > 0 and len(rows) < total_rows:
			remaining_capacity = total_rows - len(rows)
			should_add_certification = random_generator.random() < 0.62 and remaining_capacity >= 2 and planned_rows >= 2

			if should_add_certification:
				certification = unused_activity(learner, NON_TARGET_CERTS, random_generator)
				add_certification_bundle(rows, learner, certification, random_generator)
				planned_rows -= 2 if certification.related_exam_id else 1
			else:
				exam = unused_activity(learner, NON_TARGET_EXAMS, random_generator)
				completion_date = random_date(random_generator, date(2019, 1, 1), TODAY)
				add_exam_row(rows, learner, exam, completion_date)
				planned_rows -= 1


def generate_rows(total_rows: int, seed: int) -> list[dict[str, object]]:
	if total_rows < 500:
		raise ValueError("Generate at least 500 rows so the controlled target-certification cohorts fit cleanly.")

	random_generator = random.Random(seed)
	fake = Faker("en_GB")
	Faker.seed(seed)

	rows: list[dict[str, object]] = []
	used_names: set[tuple[str, str]] = set()
	add_target_cohorts(rows, fake, random_generator, used_names)
	add_non_target_rows(rows, fake, random_generator, used_names, total_rows)
	random_generator.shuffle(rows)
	return rows


def write_csv(rows: list[dict[str, object]], output_path: Path) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", newline="", encoding="utf-8") as output_file:
		writer = csv.DictWriter(output_file, fieldnames=COLUMNS)
		writer.writeheader()
		writer.writerows(rows)


def validate_output(output_path: Path, expected_rows: int) -> None:
	import pandas as pd

	dataframe = pd.read_csv(output_path)
	if len(dataframe) != expected_rows:
		raise AssertionError(f"Expected {expected_rows:,} rows, found {len(dataframe):,}.")

	expected_constants = {
		"PGAMpnId": PGAMPN_ID,
		"MPNId": PGAMPN_ID,
		"PartnerName": PARTNER_NAME,
		"PartnerCityLocation": PARTNER_CITY,
		"PartnerCountryLocation": PARTNER_COUNTRY,
		"UserCount": USER_COUNT,
	}
	for column_name, expected_value in expected_constants.items():
		actual_values = set(dataframe[column_name].dropna().unique())
		if actual_values != {expected_value}:
			raise AssertionError(f"{column_name} contains unexpected values: {actual_values}")

	expected_corp_emails = dataframe.apply(
		lambda row: contoso_email(str(row["IndividualFirstName"]), str(row["IndividualLastName"])), axis=1
	)
	expected_personal_emails = dataframe.apply(
		lambda row: personal_email(str(row["IndividualFirstName"]), str(row["IndividualLastName"])), axis=1
	)
	if not dataframe["Email"].eq(expected_personal_emails).all():
		raise AssertionError("Found Email values that do not match learner names.")
	if not dataframe["CorpEmail"].str.endswith("@contoso.com").all():
		raise AssertionError("Found CorpEmail values outside the @contoso.com domain.")
	if not dataframe["CorpEmail"].eq(expected_corp_emails).all():
		raise AssertionError("Found CorpEmail values that do not match learner names.")

	learner_keys = ["IndividualFirstName", "IndividualLastName", "CorpEmail"]
	aad_per_learner = dataframe.groupby(learner_keys)["AADUserId"].nunique()
	learners_per_aad = dataframe.groupby("AADUserId").apply(
		lambda group: group[learner_keys].drop_duplicates().shape[0], include_groups=False
	)
	if aad_per_learner.max() != 1 or learners_per_aad.max() != 1:
		raise AssertionError("AADUserId values are not mapped 1:1 with generated learners.")

	activity_titles_by_id = dataframe.groupby("TrainingActivityId")["TrainingTitle"].nunique()
	if activity_titles_by_id.max() != 1:
		raise AssertionError("A TrainingActivityId maps to multiple TrainingTitle values.")

	expiration_dates = pd.to_datetime(dataframe["ExpirationDate"], errors="coerce")
	expired_certifications = (
		(dataframe["TrainingType"] == "Certification")
		& expiration_dates.notna()
		& (expiration_dates.dt.date < TODAY)
	)
	invalid_status = dataframe.loc[expired_certifications & (dataframe["ActivationStatus"] != "Expired")]
	if not invalid_status.empty:
		raise AssertionError("Found certifications with past ExpirationDate that are not marked Expired.")

	invalid_active = dataframe.loc[(~expired_certifications) & (dataframe["ActivationStatus"] != "Active")]
	if not invalid_active.empty:
		raise AssertionError("Found rows that should be Active but are not marked Active.")

	filtered = dataframe[
		dataframe["TrainingTitle"].isin(TARGET_CERT_TITLES)
		& (dataframe["ActivationStatus"] == "Active")
		& (dataframe["TrainingType"] == "Certification")
	]
	cert_counts = filtered.groupby("AADUserId")["TrainingTitle"].nunique()
	all_three_count = int((cert_counts == 3).sum())
	two_of_three_count = int((cert_counts == 2).sum())
	one_of_three_count = int((cert_counts == 1).sum())

	at_risk = filtered.copy()
	at_risk["ExpirationDate"] = pd.to_datetime(at_risk["ExpirationDate"], errors="coerce")
	at_risk = at_risk.dropna(subset=["ExpirationDate"])
	cutoff = pd.Timestamp(TODAY) + pd.DateOffset(months=6)
	at_risk = at_risk[(at_risk["ExpirationDate"] >= pd.Timestamp(TODAY)) & (at_risk["ExpirationDate"] <= cutoff)]

	if all_three_count != DEFAULT_FULL_TARGET_LEARNERS:
		raise AssertionError(f"Expected {DEFAULT_FULL_TARGET_LEARNERS} all-three learners, found {all_three_count}.")
	if two_of_three_count != DEFAULT_TWO_TARGET_LEARNERS:
		raise AssertionError(f"Expected {DEFAULT_TWO_TARGET_LEARNERS} two-of-three learners, found {two_of_three_count}.")
	if one_of_three_count != DEFAULT_ONE_TARGET_LEARNERS:
		raise AssertionError(f"Expected {DEFAULT_ONE_TARGET_LEARNERS} one-of-three learners, found {one_of_three_count}.")

	print(f"Validated {len(dataframe):,} rows from {output_path}.")
	print(f"Unique learners: {dataframe['AADUserId'].nunique():,}")
	print(f"Learners with all 3 target certifications: {all_three_count:,}")
	print(f"Learners with exactly 2 of 3 target certifications: {two_of_three_count:,}")
	print(f"Learners with exactly 1 of 3 target certifications: {one_of_three_count:,}")
	print(f"Target certifications expiring within 6 months: {len(at_risk):,}")


def main() -> None:
	args = parse_args()
	output_path = Path(args.output)
	rows = generate_rows(args.rows, args.seed)
	write_csv(rows, output_path)
	print(f"Generated {len(rows):,} synthetic training activity rows at {output_path}.")
	if not args.skip_validation:
		validate_output(output_path, args.rows)


if __name__ == "__main__":
	main()
