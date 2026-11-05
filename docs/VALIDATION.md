# Numerical and artifact checks

The nine-step analysis pipeline was executed with the documented input checksum and pinned Python libraries. All nine steps completed.

- **71 of 71 numerical audit checks** match the presentation reference values. Three additional records are informational and are not counted as tests.
- The primary sample contains **451 matched wines** and the broader sample **459**. The frozen-key comparison reports **zero match-key drift**.
- Matched-wine result tables reproduce within floating-point precision (differences below 1e-12 in residuals). The 47 Iowa/BC spirits records reproduce as the same record set; equal-value rows can differ in display order.
- The presentation rebuild matches the included HTML page.
- Targeted browser checks cover initial rendering, changing the shelf guide from red to white, and entering presentation mode. The white US$16–25 selection identifies Muscadet as the leading group.
- The Tableau archive passes ZIP integrity and workbook XML checks and includes its linked cleaned Excel file. These structural checks do not certify Tableau rendering or interactions.

These checks establish numerical consistency and the tested artifact behavior. They do not independently validate every match, every literature claim, generalization to new data or commercial impact.
