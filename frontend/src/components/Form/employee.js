import router from "@/router"
import { createResource } from "frappe-ui"

export const employeeResource = createResource({
	url: "khanal_tech_integrations.api.employee.get_current_employee_info",
	// cache: "hrm:employee",
	onError(error) {
		if (error && error.exc_type === "AuthenticationError") {
			router.push("/login")
		}
	},
})