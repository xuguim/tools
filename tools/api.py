import frappe
import os
import json

@frappe.whitelist()
def get_customize_data():
	apps = frappe.get_installed_apps()
	data = {}
	for app in apps:
		if app in ('frappe', 'erpnext'):
			continue
		customize = get_custom_files(app)
		if customize:
			data[app] = customize
	return data

@frappe.whitelist()
def get_doctypes():
	pass

@frappe.whitelist()
def get_custom_files(app_name,doctype=None):
	modules = []
	res = {}
	for module_name in frappe.local.app_modules.get(app_name) or []:
		folder = frappe.get_app_path(app_name, module_name, "custom")
		if os.path.exists(folder):
			
			for fname in os.listdir(folder):
				if fname.endswith(".json"):
					if doctype:
						if fname != doctype.replace(' ', '_').lower() + '.json':
							continue
					with open(os.path.join(folder, fname)) as f:
						data = json.loads(f.read())
						if not module_name in modules:
							modules.append(module_name)
						if not res.get(module_name):
							res[module_name] = []
						res[module_name].append(data)
	if(len(modules) > 0):
		return {'modules':modules,'files':res}
	
@frappe.whitelist()
def get_custom_fields_and_prop_setter(app_name, doctype):
	custom_fields = frappe.get_all('Custom Field',
		filters={
			'dt': doctype,
		},
		fields = ['*']
	)
	custom_fields = [sort_dict(x) for x in custom_fields]

	property_setters = frappe.get_all('Property Setter',
		filters={
			'doctype_or_field':'DocField',
			'doc_type': doctype
		},
		fields=['*']
	)
	property_setters = [sort_dict(x) for x in property_setters]

	return {
		"custom_fields": custom_fields,
		"property_setters": property_setters,
	}

def sort_dict(doc):
	return dict(sorted(doc.items()))