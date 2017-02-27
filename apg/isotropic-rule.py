# isotropic-rule.py
# Generate a rule table for an isotropic rule using Alan Hensel's
# isotropic, non-totalistic rule format for CA on the Moore neighbourhood

import golly as g
import isotropicRulegen as isorg

rulestring = g.getstring("Enter rule string in Alan Hensel's isotropic rule notation", 
                         "B2-a/S12")

rg = isorg.RuleGenerator()

rg.setrule(rulestring)
rg.saveIsotropicRule()
g.setrule(rg.rulename)

g.show("Created rule in file: " + rg.rulename + ".rule")
