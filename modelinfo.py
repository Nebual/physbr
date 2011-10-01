#This is for model data.

#Classes: a theoretical list
#prop - a normal prop
#prop_static - imovable prop
#wire_button - something that will send a PULSE when activated
#wire_switch - something that will TOGGLE
#wire_dispenser - drop stuff
#wire_door - they get a class all of their own
#tool - tools in the form of a prop



Models = {
	#Props
	'cube':{
	'Mass':5,
	'Class':"prop"
	},
	
	'sphere':{
	'Mass':5,
	'Class':"prop",
	'Rolls':True,
	'Friction':0.2,
	},

	'table':{
	'Mass':30,
	'Class':"prop"
	},
	
	#Wire_buttons
	'button':{
	'Mass':0,
	'Class':"wire_button",
	'Physical':False
	},
	
	#Wire_switchs
	'pad':{
	'Mass':0,
	'Class':"wire_pad",
	'Physical':False
	},
	
	'magnetic-pad':{
	'Mass':0,
	'Class':"wire_magneticpad",
	'Physical':False
	},
	
	'switch':{
	'Mass':0,
	'Class':"wire_switch",
	'Physical':False
	},
	
	#Wire_Dispensers
	'dispenser':{
	'Mass':0,
	'Class':"wire_dispenser"
	},
	
	#Wire_Doors
	'door-left':{
	'Mass':0,
	'Class':"wire_door"
	},
	
	'door-right':{
	'Mass':0,
	'Class':"wire_door"
	}
}