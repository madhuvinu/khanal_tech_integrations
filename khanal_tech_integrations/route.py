routes=[
	# Legacy intranet routes
	{'from_route': '/intranet/deliveryhistory/<docentry>','to_route':'intranet/deliveryhistory'},
	
	# Kiosk static assets (must come before kiosk routes)
	{'from_route': '/kiosk/assets/<path:path>','to_route':'kiosk_static'},
	{'from_route': '/kiosk/manifest.webmanifest','to_route':'kiosk_static'},
	{'from_route': '/kiosk/sw.js','to_route':'kiosk_static'},
	{'from_route': '/kiosk/workbox-<path:path>','to_route':'kiosk_static'},
	{'from_route': '/kiosk/registerSW.js','to_route':'kiosk_static'},
	
	# Kiosk test page (development only)
	{'from_route': '/kiosk-test','to_route':'kiosk_test'},
	
	# Main kiosk SPA routes (explicit to avoid catching assets)
	{'from_route': '/kiosk','to_route':'kiosk'},
	{'from_route': '/kiosk/login','to_route':'kiosk'},
	{'from_route': '/kiosk/plant-selection','to_route':'kiosk'},
	{'from_route': '/kiosk/login/<plant_id>','to_route':'kiosk'},
	
	# Plant-specific routes
	{'from_route': '/kiosk/plant/<plant_id>','to_route':'kiosk'},
	{'from_route': '/kiosk/plant/<plant_id>/dashboard','to_route':'kiosk'},
	{'from_route': '/kiosk/plant/<plant_id>/grn','to_route':'kiosk'},
	{'from_route': '/kiosk/plant/<plant_id>/production-order','to_route':'kiosk'},
	{'from_route': '/kiosk/plant/<plant_id>/quality','to_route':'kiosk'},
	{'from_route': '/kiosk/plant/<plant_id>/inventory-transfer','to_route':'kiosk'},
	{'from_route': '/kiosk/plant/<plant_id>/<feature>','to_route':'kiosk'},
	
	# API routes for kiosk
	{'from_route': '/api/kiosk/<path:path>','to_route':'kiosk_api'},
	
	# Admin routes
	{'from_route': '/kiosk/admin','to_route':'kiosk'},
	{'from_route': '/kiosk/admin/<path:path>','to_route':'kiosk'},
	
	# Catch-all for any other kiosk routes (must be last)
	{'from_route': '/kiosk/<path:path>','to_route':'kiosk'}
]