I want a webapp:

Database:
SQLite

Backend:
FastAPI

Frontend:
Svelte

Deployment:
docker on VPS, github CI/CD


App to track the medicine of my grandma.

- Drugplan (and the ability to change it) with data for each drug (size of the package (how many pills per pkg, dosage)), current amount of pills left
- Mail Reminder to set up the drugs for the week
- Mail Reminder to re-order the drugs if less than 3 weeks of pills are left
  - also reminder if its the first order in the quartal (need to show insurance card once at the doctor)

in depth guide on how to set it all up, deploy and link it to a porkbun subdomain

rules:
1. keep it simple
2. keep it private
3. google style docstrings
4. Please also write an explainer for each component you create. I dont know fastapi and svelte and want to learn these technologies
