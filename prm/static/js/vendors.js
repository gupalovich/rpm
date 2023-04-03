// UMD insanity
// This code sets up support for (in order) AMD, ES6 modules, and globals.
(function (root, factory) {
    //@ts-ignore
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        //@ts-ignore
        define([], factory);
    } else if (typeof module === 'object' && module.exports) {
        // Node. Does not work with strict CommonJS, but
        // only CommonJS-like environments that support module.exports,
        // like Node.
        module.exports = factory();
    } else {
        // Browser globals
        root.htmx = root.htmx || factory();
    }
}(typeof self !== 'undefined' ? self : this, function () {
return (function () {
        'use strict';

        // Public API
        //** @type {import("./htmx").HtmxApi} */
        // TODO: list all methods in public API
        var htmx = {
            onLoad: onLoadHelper,
            process: processNode,
            on: addEventListenerImpl,
            off: removeEventListenerImpl,
            trigger : triggerEvent,
            ajax : ajaxHelper,
            find : find,
            findAll : findAll,
            closest : closest,
            values : function(elt, type){
                var inputValues = getInputValues(elt, type || "post");
                return inputValues.values;
            },
            remove : removeElement,
            addClass : addClassToElement,
            removeClass : removeClassFromElement,
            toggleClass : toggleClassOnElement,
            takeClass : takeClassForElement,
            defineExtension : defineExtension,
            removeExtension : removeExtension,
            logAll : logAll,
            logger : null,
            config : {
                historyEnabled:true,
                historyCacheSize:10,
                refreshOnHistoryMiss:false,
                defaultSwapStyle:'innerHTML',
                defaultSwapDelay:0,
                defaultSettleDelay:20,
                includeIndicatorStyles:true,
                indicatorClass:'htmx-indicator',
                requestClass:'htmx-request',
                addedClass:'htmx-added',
                settlingClass:'htmx-settling',
                swappingClass:'htmx-swapping',
                allowEval:true,
                inlineScriptNonce:'',
                attributesToSettle:["class", "style", "width", "height"],
                withCredentials:false,
                timeout:0,
                wsReconnectDelay: 'full-jitter',
                wsBinaryType: 'blob',
                disableSelector: "[hx-disable], [data-hx-disable]",
                useTemplateFragments: false,
                scrollBehavior: 'smooth',
                defaultFocusScroll: false,
                getCacheBusterParam: false,
            },
            parseInterval:parseInterval,
            _:internalEval,
            createEventSource: function(url){
                return new EventSource(url, {withCredentials:true})
            },
            createWebSocket: function(url){
                var sock = new WebSocket(url, []);
                sock.binaryType = htmx.config.wsBinaryType;
                return sock;
            },
            version: "1.8.6"
        };

        /** @type {import("./htmx").HtmxInternalApi} */
        var internalAPI = {
            addTriggerHandler: addTriggerHandler,
            bodyContains: bodyContains,
            canAccessLocalStorage: canAccessLocalStorage,
            filterValues: filterValues,
            hasAttribute: hasAttribute,
            getAttributeValue: getAttributeValue,
            getClosestMatch: getClosestMatch,
            getExpressionVars: getExpressionVars,
            getHeaders: getHeaders,
            getInputValues: getInputValues,
            getInternalData: getInternalData,
            getSwapSpecification: getSwapSpecification,
            getTriggerSpecs: getTriggerSpecs,
            getTarget: getTarget,
            makeFragment: makeFragment,
            mergeObjects: mergeObjects,
            makeSettleInfo: makeSettleInfo,
            oobSwap: oobSwap,
            selectAndSwap: selectAndSwap,
            settleImmediately: settleImmediately,
            shouldCancel: shouldCancel,
            triggerEvent: triggerEvent,
            triggerErrorEvent: triggerErrorEvent,
            withExtensions: withExtensions,
        }

        var VERBS = ['get', 'post', 'put', 'delete', 'patch'];
        var VERB_SELECTOR = VERBS.map(function(verb){
            return "[hx-" + verb + "], [data-hx-" + verb + "]"
        }).join(", ");

        //====================================================================
        // Utilities
        //====================================================================

        function parseInterval(str) {
            if (str == undefined)  {
                return undefined
            }
            if (str.slice(-2) == "ms") {
                return parseFloat(str.slice(0,-2)) || undefined
            }
            if (str.slice(-1) == "s") {
                return (parseFloat(str.slice(0,-1)) * 1000) || undefined
            }
            if (str.slice(-1) == "m") {
                return (parseFloat(str.slice(0,-1)) * 1000 * 60) || undefined
            }
            return parseFloat(str) || undefined
        }

        /**
         * @param {HTMLElement} elt
         * @param {string} name
         * @returns {(string | null)}
         */
        function getRawAttribute(elt, name) {
            return elt.getAttribute && elt.getAttribute(name);
        }

        // resolve with both hx and data-hx prefixes
        function hasAttribute(elt, qualifiedName) {
            return elt.hasAttribute && (elt.hasAttribute(qualifiedName) ||
                elt.hasAttribute("data-" + qualifiedName));
        }

        /**
         *
         * @param {HTMLElement} elt
         * @param {string} qualifiedName
         * @returns {(string | null)}
         */
        function getAttributeValue(elt, qualifiedName) {
            return getRawAttribute(elt, qualifiedName) || getRawAttribute(elt, "data-" + qualifiedName);
        }

        /**
         * @param {HTMLElement} elt
         * @returns {HTMLElement | null}
         */
        function parentElt(elt) {
            return elt.parentElement;
        }

        /**
         * @returns {Document}
         */
        function getDocument() {
            return document;
        }

        /**
         * @param {HTMLElement} elt
         * @param {(e:HTMLElement) => boolean} condition
         * @returns {HTMLElement | null}
         */
        function getClosestMatch(elt, condition) {
            while (elt && !condition(elt)) {
                elt = parentElt(elt);
            }

            return elt ? elt : null;
        }

        function getAttributeValueWithDisinheritance(initialElement, ancestor, attributeName){
            var attributeValue = getAttributeValue(ancestor, attributeName);
            var disinherit = getAttributeValue(ancestor, "hx-disinherit");
            if (initialElement !== ancestor && disinherit && (disinherit === "*" || disinherit.split(" ").indexOf(attributeName) >= 0)) {
                return "unset";
            } else {
                return attributeValue
            }
        }

        /**
         * @param {HTMLElement} elt
         * @param {string} attributeName
         * @returns {string | null}
         */
        function getClosestAttributeValue(elt, attributeName) {
            var closestAttr = null;
            getClosestMatch(elt, function (e) {
                return closestAttr = getAttributeValueWithDisinheritance(elt, e, attributeName);
            });
            if (closestAttr !== "unset") {
                return closestAttr;
            }
        }

        /**
         * @param {HTMLElement} elt
         * @param {string} selector
         * @returns {boolean}
         */
        function matches(elt, selector) {
            // @ts-ignore: non-standard properties for browser compatability
            // noinspection JSUnresolvedVariable
            var matchesFunction = elt.matches || elt.matchesSelector || elt.msMatchesSelector || elt.mozMatchesSelector || elt.webkitMatchesSelector || elt.oMatchesSelector;
            return matchesFunction && matchesFunction.call(elt, selector);
        }

        /**
         * @param {string} str
         * @returns {string}
         */
        function getStartTag(str) {
            var tagMatcher = /<([a-z][^\/\0>\x20\t\r\n\f]*)/i
            var match = tagMatcher.exec( str );
            if (match) {
                return match[1].toLowerCase();
            } else {
                return "";
            }
        }

        /**
         *
         * @param {string} resp
         * @param {number} depth
         * @returns {Element}
         */
        function parseHTML(resp, depth) {
            var parser = new DOMParser();
            var responseDoc = parser.parseFromString(resp, "text/html");

            /** @type {Element} */
            var responseNode = responseDoc.body;
            while (depth > 0) {
                depth--;
                // @ts-ignore
                responseNode = responseNode.firstChild;
            }
            if (responseNode == null) {
                // @ts-ignore
                responseNode = getDocument().createDocumentFragment();
            }
            return responseNode;
        }

        /**
         *
         * @param {string} resp
         * @returns {Element}
         */
        function makeFragment(resp) {
            if (htmx.config.useTemplateFragments) {
                var documentFragment = parseHTML("<body><template>" + resp + "</template></body>", 0);
                // @ts-ignore type mismatch between DocumentFragment and Element.
                // TODO: Are these close enough for htmx to use interchangably?
                return documentFragment.querySelector('template').content;
            } else {
                var startTag = getStartTag(resp);
                switch (startTag) {
                    case "thead":
                    case "tbody":
                    case "tfoot":
                    case "colgroup":
                    case "caption":
                        return parseHTML("<table>" + resp + "</table>", 1);
                    case "col":
                        return parseHTML("<table><colgroup>" + resp + "</colgroup></table>", 2);
                    case "tr":
                        return parseHTML("<table><tbody>" + resp + "</tbody></table>", 2);
                    case "td":
                    case "th":
                        return parseHTML("<table><tbody><tr>" + resp + "</tr></tbody></table>", 3);
                    case "script":
                        return parseHTML("<div>" + resp + "</div>", 1);
                    default:
                        return parseHTML(resp, 0);
                }
            }
        }

        /**
         * @param {Function} func
         */
        function maybeCall(func){
            if(func) {
                func();
            }
        }

        /**
         * @param {any} o
         * @param {string} type
         * @returns
         */
        function isType(o, type) {
            return Object.prototype.toString.call(o) === "[object " + type + "]";
        }

        /**
         * @param {*} o
         * @returns {o is Function}
         */
        function isFunction(o) {
            return isType(o, "Function");
        }

        /**
         * @param {*} o
         * @returns {o is Object}
         */
        function isRawObject(o) {
            return isType(o, "Object");
        }

        /**
         * getInternalData retrieves "private" data stored by htmx within an element
         * @param {HTMLElement} elt
         * @returns {*}
         */
        function getInternalData(elt) {
            var dataProp = 'htmx-internal-data';
            var data = elt[dataProp];
            if (!data) {
                data = elt[dataProp] = {};
            }
            return data;
        }

        /**
         * toArray converts an ArrayLike object into a real array.
         * @param {ArrayLike} arr
         * @returns {any[]}
         */
        function toArray(arr) {
            var returnArr = [];
            if (arr) {
                for (var i = 0; i < arr.length; i++) {
                    returnArr.push(arr[i]);
                }
            }
            return returnArr
        }

        function forEach(arr, func) {
            if (arr) {
                for (var i = 0; i < arr.length; i++) {
                    func(arr[i]);
                }
            }
        }

        function isScrolledIntoView(el) {
            var rect = el.getBoundingClientRect();
            var elemTop = rect.top;
            var elemBottom = rect.bottom;
            return elemTop < window.innerHeight && elemBottom >= 0;
        }

        function bodyContains(elt) {
            // IE Fix
            if (elt.getRootNode && elt.getRootNode() instanceof ShadowRoot) {
                return getDocument().body.contains(elt.getRootNode().host);
            } else {
                return getDocument().body.contains(elt);
            }
        }

        function splitOnWhitespace(trigger) {
            return trigger.trim().split(/\s+/);
        }

        /**
         * mergeObjects takes all of the keys from
         * obj2 and duplicates them into obj1
         * @param {Object} obj1
         * @param {Object} obj2
         * @returns {Object}
         */
        function mergeObjects(obj1, obj2) {
            for (var key in obj2) {
                if (obj2.hasOwnProperty(key)) {
                    obj1[key] = obj2[key];
                }
            }
            return obj1;
        }

        function parseJSON(jString) {
            try {
                return JSON.parse(jString);
            } catch(error) {
                logError(error);
                return null;
            }
        }

        function canAccessLocalStorage() {
            var test = 'htmx:localStorageTest';
            try {
                localStorage.setItem(test, test);
                localStorage.removeItem(test);
                return true;
            } catch(e) {
                return false;
            }
        }

        //==========================================================================================
        // public API
        //==========================================================================================

        function internalEval(str){
            return maybeEval(getDocument().body, function () {
                return eval(str);
            });
        }

        function onLoadHelper(callback) {
            var value = htmx.on("htmx:load", function(evt) {
                callback(evt.detail.elt);
            });
            return value;
        }

        function logAll(){
            htmx.logger = function(elt, event, data) {
                if(console) {
                    console.log(event, elt, data);
                }
            }
        }

        function find(eltOrSelector, selector) {
            if (selector) {
                return eltOrSelector.querySelector(selector);
            } else {
                return find(getDocument(), eltOrSelector);
            }
        }

        function findAll(eltOrSelector, selector) {
            if (selector) {
                return eltOrSelector.querySelectorAll(selector);
            } else {
                return findAll(getDocument(), eltOrSelector);
            }
        }

        function removeElement(elt, delay) {
            elt = resolveTarget(elt);
            if (delay) {
                setTimeout(function(){removeElement(elt);}, delay)
            } else {
                elt.parentElement.removeChild(elt);
            }
        }

        function addClassToElement(elt, clazz, delay) {
            elt = resolveTarget(elt);
            if (delay) {
                setTimeout(function(){addClassToElement(elt, clazz);}, delay)
            } else {
                elt.classList && elt.classList.add(clazz);
            }
        }

        function removeClassFromElement(elt, clazz, delay) {
            elt = resolveTarget(elt);
            if (delay) {
                setTimeout(function(){removeClassFromElement(elt, clazz);}, delay)
            } else {
                if (elt.classList) {
                    elt.classList.remove(clazz);
                    // if there are no classes left, remove the class attribute
                    if (elt.classList.length === 0) {
                        elt.removeAttribute("class");
                    }
                }
            }
        }

        function toggleClassOnElement(elt, clazz) {
            elt = resolveTarget(elt);
            elt.classList.toggle(clazz);
        }

        function takeClassForElement(elt, clazz) {
            elt = resolveTarget(elt);
            forEach(elt.parentElement.children, function(child){
                removeClassFromElement(child, clazz);
            })
            addClassToElement(elt, clazz);
        }

        function closest(elt, selector) {
            elt = resolveTarget(elt);
            if (elt.closest) {
                return elt.closest(selector);
            } else {
                // TODO remove when IE goes away
                do{
                    if (elt == null || matches(elt, selector)){
                        return elt;
                    }
                }
                while (elt = elt && parentElt(elt));
                return null;
            }
        }

        function querySelectorAllExt(elt, selector) {
            if (selector.indexOf("closest ") === 0) {
                return [closest(elt, selector.substr(8))];
            } else if (selector.indexOf("find ") === 0) {
                return [find(elt, selector.substr(5))];
            } else if (selector.indexOf("next ") === 0) {
                return [scanForwardQuery(elt, selector.substr(5))];
            } else if (selector.indexOf("previous ") === 0) {
                return [scanBackwardsQuery(elt, selector.substr(9))];
            } else if (selector === 'document') {
                return [document];
            } else if (selector === 'window') {
                return [window];
            } else {
                return getDocument().querySelectorAll(selector);
            }
        }

        var scanForwardQuery = function(start, match) {
            var results = getDocument().querySelectorAll(match);
            for (var i = 0; i < results.length; i++) {
                var elt = results[i];
                if (elt.compareDocumentPosition(start) === Node.DOCUMENT_POSITION_PRECEDING) {
                    return elt;
                }
            }
        }

        var scanBackwardsQuery = function(start, match) {
            var results = getDocument().querySelectorAll(match);
            for (var i = results.length - 1; i >= 0; i--) {
                var elt = results[i];
                if (elt.compareDocumentPosition(start) === Node.DOCUMENT_POSITION_FOLLOWING) {
                    return elt;
                }
            }
        }

        function querySelectorExt(eltOrSelector, selector) {
            if (selector) {
                return querySelectorAllExt(eltOrSelector, selector)[0];
            } else {
                return querySelectorAllExt(getDocument().body, eltOrSelector)[0];
            }
        }

        function resolveTarget(arg2) {
            if (isType(arg2, 'String')) {
                return find(arg2);
            } else {
                return arg2;
            }
        }

        function processEventArgs(arg1, arg2, arg3) {
            if (isFunction(arg2)) {
                return {
                    target: getDocument().body,
                    event: arg1,
                    listener: arg2
                }
            } else {
                return {
                    target: resolveTarget(arg1),
                    event: arg2,
                    listener: arg3
                }
            }

        }

        function addEventListenerImpl(arg1, arg2, arg3) {
            ready(function(){
                var eventArgs = processEventArgs(arg1, arg2, arg3);
                eventArgs.target.addEventListener(eventArgs.event, eventArgs.listener);
            })
            var b = isFunction(arg2);
            return b ? arg2 : arg3;
        }

        function removeEventListenerImpl(arg1, arg2, arg3) {
            ready(function(){
                var eventArgs = processEventArgs(arg1, arg2, arg3);
                eventArgs.target.removeEventListener(eventArgs.event, eventArgs.listener);
            })
            return isFunction(arg2) ? arg2 : arg3;
        }

        //====================================================================
        // Node processing
        //====================================================================

        var DUMMY_ELT = getDocument().createElement("output"); // dummy element for bad selectors
        function findAttributeTargets(elt, attrName) {
            var attrTarget = getClosestAttributeValue(elt, attrName);
            if (attrTarget) {
                if (attrTarget === "this") {
                    return [findThisElement(elt, attrName)];
                } else {
                    var result = querySelectorAllExt(elt, attrTarget);
                    if (result.length === 0) {
                        logError('The selector "' + attrTarget + '" on ' + attrName + " returned no matches!");
                        return [DUMMY_ELT]
                    } else {
                        return result;
                    }
                }
            }
        }

        function findThisElement(elt, attribute){
            return getClosestMatch(elt, function (elt) {
                return getAttributeValue(elt, attribute) != null;
            })
        }

        function getTarget(elt) {
            var targetStr = getClosestAttributeValue(elt, "hx-target");
            if (targetStr) {
                if (targetStr === "this") {
                    return findThisElement(elt,'hx-target');
                } else {
                    return querySelectorExt(elt, targetStr)
                }
            } else {
                var data = getInternalData(elt);
                if (data.boosted) {
                    return getDocument().body;
                } else {
                    return elt;
                }
            }
        }

        function shouldSettleAttribute(name) {
            var attributesToSettle = htmx.config.attributesToSettle;
            for (var i = 0; i < attributesToSettle.length; i++) {
                if (name === attributesToSettle[i]) {
                    return true;
                }
            }
            return false;
        }

        function cloneAttributes(mergeTo, mergeFrom) {
            forEach(mergeTo.attributes, function (attr) {
                if (!mergeFrom.hasAttribute(attr.name) && shouldSettleAttribute(attr.name)) {
                    mergeTo.removeAttribute(attr.name)
                }
            });
            forEach(mergeFrom.attributes, function (attr) {
                if (shouldSettleAttribute(attr.name)) {
                    mergeTo.setAttribute(attr.name, attr.value);
                }
            });
        }

        function isInlineSwap(swapStyle, target) {
            var extensions = getExtensions(target);
            for (var i = 0; i < extensions.length; i++) {
                var extension = extensions[i];
                try {
                    if (extension.isInlineSwap(swapStyle)) {
                        return true;
                    }
                } catch(e) {
                    logError(e);
                }
            }
            return swapStyle === "outerHTML";
        }

        /**
         *
         * @param {string} oobValue
         * @param {HTMLElement} oobElement
         * @param {*} settleInfo
         * @returns
         */
        function oobSwap(oobValue, oobElement, settleInfo) {
            var selector = "#" + oobElement.id;
            var swapStyle = "outerHTML";
            if (oobValue === "true") {
                // do nothing
            } else if (oobValue.indexOf(":") > 0) {
                swapStyle = oobValue.substr(0, oobValue.indexOf(":"));
                selector  = oobValue.substr(oobValue.indexOf(":") + 1, oobValue.length);
            } else {
                swapStyle = oobValue;
            }

            var targets = getDocument().querySelectorAll(selector);
            if (targets) {
                forEach(
                    targets,
                    function (target) {
                        var fragment;
                        var oobElementClone = oobElement.cloneNode(true);
                        fragment = getDocument().createDocumentFragment();
                        fragment.appendChild(oobElementClone);
                        if (!isInlineSwap(swapStyle, target)) {
                            fragment = oobElementClone; // if this is not an inline swap, we use the content of the node, not the node itself
                        }

                        var beforeSwapDetails = {shouldSwap: true, target: target, fragment:fragment };
                        if (!triggerEvent(target, 'htmx:oobBeforeSwap', beforeSwapDetails)) return;

                        target = beforeSwapDetails.target; // allow re-targeting
                        if (beforeSwapDetails['shouldSwap']){
                            swap(swapStyle, target, target, fragment, settleInfo);
                        }
                        forEach(settleInfo.elts, function (elt) {
                            triggerEvent(elt, 'htmx:oobAfterSwap', beforeSwapDetails);
                        });
                    }
                );
                oobElement.parentNode.removeChild(oobElement);
            } else {
                oobElement.parentNode.removeChild(oobElement);
                triggerErrorEvent(getDocument().body, "htmx:oobErrorNoTarget", {content: oobElement});
            }
            return oobValue;
        }

        function handleOutOfBandSwaps(elt, fragment, settleInfo) {
            var oobSelects = getClosestAttributeValue(elt, "hx-select-oob");
            if (oobSelects) {
                var oobSelectValues = oobSelects.split(",");
                for (let i = 0; i < oobSelectValues.length; i++) {
                    var oobSelectValue = oobSelectValues[i].split(":", 2);
                    var id = oobSelectValue[0];
                    if (id.indexOf("#") === 0) {
                        id = id.substring(1);
                    }
                    var oobValue = oobSelectValue[1] || "true";
                    var oobElement = fragment.querySelector("#" + id);
                    if (oobElement) {
                        oobSwap(oobValue, oobElement, settleInfo);
                    }
                }
            }
            forEach(findAll(fragment, '[hx-swap-oob], [data-hx-swap-oob]'), function (oobElement) {
                var oobValue = getAttributeValue(oobElement, "hx-swap-oob");
                if (oobValue != null) {
                    oobSwap(oobValue, oobElement, settleInfo);
                }
            });
        }

        function handlePreservedElements(fragment) {
            forEach(findAll(fragment, '[hx-preserve], [data-hx-preserve]'), function (preservedElt) {
                var id = getAttributeValue(preservedElt, "id");
                var oldElt = getDocument().getElementById(id);
                if (oldElt != null) {
                    preservedElt.parentNode.replaceChild(oldElt, preservedElt);
                }
            });
        }

        function handleAttributes(parentNode, fragment, settleInfo) {
            forEach(fragment.querySelectorAll("[id]"), function (newNode) {
                if (newNode.id && newNode.id.length > 0) {
                    var normalizedId = newNode.id.replace("'", "\\'");
                    var oldNode = parentNode.querySelector(newNode.tagName + "[id='" + normalizedId + "']");
                    if (oldNode && oldNode !== parentNode) {
                        var newAttributes = newNode.cloneNode();
                        cloneAttributes(newNode, oldNode);
                        settleInfo.tasks.push(function () {
                            cloneAttributes(newNode, newAttributes);
                        });
                    }
                }
            });
        }

        function makeAjaxLoadTask(child) {
            return function () {
                removeClassFromElement(child, htmx.config.addedClass);
                processNode(child);
                processScripts(child);
                processFocus(child)
                triggerEvent(child, 'htmx:load');
            };
        }

        function processFocus(child) {
            var autofocus = "[autofocus]";
            var autoFocusedElt = matches(child, autofocus) ? child : child.querySelector(autofocus)
            if (autoFocusedElt != null) {
                autoFocusedElt.focus();
            }
        }

        function insertNodesBefore(parentNode, insertBefore, fragment, settleInfo) {
            handleAttributes(parentNode, fragment, settleInfo);
            while(fragment.childNodes.length > 0){
                var child = fragment.firstChild;
                addClassToElement(child, htmx.config.addedClass);
                parentNode.insertBefore(child, insertBefore);
                if (child.nodeType !== Node.TEXT_NODE && child.nodeType !== Node.COMMENT_NODE) {
                    settleInfo.tasks.push(makeAjaxLoadTask(child));
                }
            }
        }

        // based on https://gist.github.com/hyamamoto/fd435505d29ebfa3d9716fd2be8d42f0,
        // derived from Java's string hashcode implementation
        function stringHash(string, hash) {
            var char = 0;
            while (char < string.length){
                hash = (hash << 5) - hash + string.charCodeAt(char++) | 0; // bitwise or ensures we have a 32-bit int
            }
            return hash;
        }

        function attributeHash(elt) {
            var hash = 0;
            // IE fix
            if (elt.attributes) {
                for (var i = 0; i < elt.attributes.length; i++) {
                    var attribute = elt.attributes[i];
                    if(attribute.value){ // only include attributes w/ actual values (empty is same as non-existent)
                        hash = stringHash(attribute.name, hash);
                        hash = stringHash(attribute.value, hash);
                    }
                }
            }
            return hash;
        }

        function deInitNode(element) {
            var internalData = getInternalData(element);
            if (internalData.webSocket) {
                internalData.webSocket.close();
            }
            if (internalData.sseEventSource) {
                internalData.sseEventSource.close();
            }
            if (internalData.listenerInfos) {
                forEach(internalData.listenerInfos, function (info) {
                    if (info.on) {
                        info.on.removeEventListener(info.trigger, info.listener);
                    }
                });
            }
        }

        function cleanUpElement(element) {
            triggerEvent(element, "htmx:beforeCleanupElement")
            deInitNode(element);
            if (element.children) { // IE
                forEach(element.children, function(child) { cleanUpElement(child) });
            }
        }

        function swapOuterHTML(target, fragment, settleInfo) {
            if (target.tagName === "BODY") {
                return swapInnerHTML(target, fragment, settleInfo);
            } else {
                // @type {HTMLElement}
                var newElt
                var eltBeforeNewContent = target.previousSibling;
                insertNodesBefore(parentElt(target), target, fragment, settleInfo);
                if (eltBeforeNewContent == null) {
                    newElt = parentElt(target).firstChild;
                } else {
                    newElt = eltBeforeNewContent.nextSibling;
                }
                getInternalData(target).replacedWith = newElt; // tuck away so we can fire events on it later
                settleInfo.elts = [] // clear existing elements
                while(newElt && newElt !== target) {
                    if (newElt.nodeType === Node.ELEMENT_NODE) {
                        settleInfo.elts.push(newElt);
                    }
                    newElt = newElt.nextElementSibling;
                }
                cleanUpElement(target);
                parentElt(target).removeChild(target);
            }
        }

        function swapAfterBegin(target, fragment, settleInfo) {
            return insertNodesBefore(target, target.firstChild, fragment, settleInfo);
        }

        function swapBeforeBegin(target, fragment, settleInfo) {
            return insertNodesBefore(parentElt(target), target, fragment, settleInfo);
        }

        function swapBeforeEnd(target, fragment, settleInfo) {
            return insertNodesBefore(target, null, fragment, settleInfo);
        }

        function swapAfterEnd(target, fragment, settleInfo) {
            return insertNodesBefore(parentElt(target), target.nextSibling, fragment, settleInfo);
        }
        function swapDelete(target, fragment, settleInfo) {
            cleanUpElement(target);
            return parentElt(target).removeChild(target);
        }

        function swapInnerHTML(target, fragment, settleInfo) {
            var firstChild = target.firstChild;
            insertNodesBefore(target, firstChild, fragment, settleInfo);
            if (firstChild) {
                while (firstChild.nextSibling) {
                    cleanUpElement(firstChild.nextSibling)
                    target.removeChild(firstChild.nextSibling);
                }
                cleanUpElement(firstChild)
                target.removeChild(firstChild);
            }
        }

        function maybeSelectFromResponse(elt, fragment) {
            var selector = getClosestAttributeValue(elt, "hx-select");
            if (selector) {
                var newFragment = getDocument().createDocumentFragment();
                forEach(fragment.querySelectorAll(selector), function (node) {
                    newFragment.appendChild(node);
                });
                fragment = newFragment;
            }
            return fragment;
        }

        function swap(swapStyle, elt, target, fragment, settleInfo) {
            switch (swapStyle) {
                case "none":
                    return;
                case "outerHTML":
                    swapOuterHTML(target, fragment, settleInfo);
                    return;
                case "afterbegin":
                    swapAfterBegin(target, fragment, settleInfo);
                    return;
                case "beforebegin":
                    swapBeforeBegin(target, fragment, settleInfo);
                    return;
                case "beforeend":
                    swapBeforeEnd(target, fragment, settleInfo);
                    return;
                case "afterend":
                    swapAfterEnd(target, fragment, settleInfo);
                    return;
                case "delete":
                    swapDelete(target, fragment, settleInfo);
                    return;
                default:
                    var extensions = getExtensions(elt);
                    for (var i = 0; i < extensions.length; i++) {
                        var ext = extensions[i];
                        try {
                            var newElements = ext.handleSwap(swapStyle, target, fragment, settleInfo);
                            if (newElements) {
                                if (typeof newElements.length !== 'undefined') {
                                    // if handleSwap returns an array (like) of elements, we handle them
                                    for (var j = 0; j < newElements.length; j++) {
                                        var child = newElements[j];
                                        if (child.nodeType !== Node.TEXT_NODE && child.nodeType !== Node.COMMENT_NODE) {
                                            settleInfo.tasks.push(makeAjaxLoadTask(child));
                                        }
                                    }
                                }
                                return;
                            }
                        } catch (e) {
                            logError(e);
                        }
                    }
                    if (swapStyle === "innerHTML") {
                        swapInnerHTML(target, fragment, settleInfo);
                    } else {
                        swap(htmx.config.defaultSwapStyle, elt, target, fragment, settleInfo);
                    }
            }
        }

        function findTitle(content) {
            if (content.indexOf('<title') > -1) {
                var contentWithSvgsRemoved = content.replace(/<svg(\s[^>]*>|>)([\s\S]*?)<\/svg>/gim, '');
                var result = contentWithSvgsRemoved.match(/<title(\s[^>]*>|>)([\s\S]*?)<\/title>/im);

                if (result) {
                    return result[2];
                }
            }
        }

        function selectAndSwap(swapStyle, target, elt, responseText, settleInfo) {
            settleInfo.title = findTitle(responseText);
            var fragment = makeFragment(responseText);
            if (fragment) {
                handleOutOfBandSwaps(elt, fragment, settleInfo);
                fragment = maybeSelectFromResponse(elt, fragment);
                handlePreservedElements(fragment);
                return swap(swapStyle, elt, target, fragment, settleInfo);
            }
        }

        function handleTrigger(xhr, header, elt) {
            var triggerBody = xhr.getResponseHeader(header);
            if (triggerBody.indexOf("{") === 0) {
                var triggers = parseJSON(triggerBody);
                for (var eventName in triggers) {
                    if (triggers.hasOwnProperty(eventName)) {
                        var detail = triggers[eventName];
                        if (!isRawObject(detail)) {
                            detail = {"value": detail}
                        }
                        triggerEvent(elt, eventName, detail);
                    }
                }
            } else {
                triggerEvent(elt, triggerBody, []);
            }
        }

        var WHITESPACE = /\s/;
        var WHITESPACE_OR_COMMA = /[\s,]/;
        var SYMBOL_START = /[_$a-zA-Z]/;
        var SYMBOL_CONT = /[_$a-zA-Z0-9]/;
        var STRINGISH_START = ['"', "'", "/"];
        var NOT_WHITESPACE = /[^\s]/;
        function tokenizeString(str) {
            var tokens = [];
            var position = 0;
            while (position < str.length) {
                if(SYMBOL_START.exec(str.charAt(position))) {
                    var startPosition = position;
                    while (SYMBOL_CONT.exec(str.charAt(position + 1))) {
                        position++;
                    }
                    tokens.push(str.substr(startPosition, position - startPosition + 1));
                } else if (STRINGISH_START.indexOf(str.charAt(position)) !== -1) {
                    var startChar = str.charAt(position);
                    var startPosition = position;
                    position++;
                    while (position < str.length && str.charAt(position) !== startChar ) {
                        if (str.charAt(position) === "\\") {
                            position++;
                        }
                        position++;
                    }
                    tokens.push(str.substr(startPosition, position - startPosition + 1));
                } else {
                    var symbol = str.charAt(position);
                    tokens.push(symbol);
                }
                position++;
            }
            return tokens;
        }

        function isPossibleRelativeReference(token, last, paramName) {
            return SYMBOL_START.exec(token.charAt(0)) &&
                token !== "true" &&
                token !== "false" &&
                token !== "this" &&
                token !== paramName &&
                last !== ".";
        }

        function maybeGenerateConditional(elt, tokens, paramName) {
            if (tokens[0] === '[') {
                tokens.shift();
                var bracketCount = 1;
                var conditionalSource = " return (function(" + paramName + "){ return (";
                var last = null;
                while (tokens.length > 0) {
                    var token = tokens[0];
                    if (token === "]") {
                        bracketCount--;
                        if (bracketCount === 0) {
                            if (last === null) {
                                conditionalSource = conditionalSource + "true";
                            }
                            tokens.shift();
                            conditionalSource += ")})";
                            try {
                                var conditionFunction = maybeEval(elt,function () {
                                    return Function(conditionalSource)();
                                    },
                                    function(){return true})
                                conditionFunction.source = conditionalSource;
                                return conditionFunction;
                            } catch (e) {
                                triggerErrorEvent(getDocument().body, "htmx:syntax:error", {error:e, source:conditionalSource})
                                return null;
                            }
                        }
                    } else if (token === "[") {
                        bracketCount++;
                    }
                    if (isPossibleRelativeReference(token, last, paramName)) {
                            conditionalSource += "((" + paramName + "." + token + ") ? (" + paramName + "." + token + ") : (window." + token + "))";
                    } else {
                        conditionalSource = conditionalSource + token;
                    }
                    last = tokens.shift();
                }
            }
        }

        function consumeUntil(tokens, match) {
            var result = "";
            while (tokens.length > 0 && !tokens[0].match(match)) {
                result += tokens.shift();
            }
            return result;
        }

        var INPUT_SELECTOR = 'input, textarea, select';

        /**
         * @param {HTMLElement} elt
         * @returns {import("./htmx").HtmxTriggerSpecification[]}
         */
        function getTriggerSpecs(elt) {
            var explicitTrigger = getAttributeValue(elt, 'hx-trigger');
            var triggerSpecs = [];
            if (explicitTrigger) {
                var tokens = tokenizeString(explicitTrigger);
                do {
                    consumeUntil(tokens, NOT_WHITESPACE);
                    var initialLength = tokens.length;
                    var trigger = consumeUntil(tokens, /[,\[\s]/);
                    if (trigger !== "") {
                        if (trigger === "every") {
                            var every = {trigger: 'every'};
                            consumeUntil(tokens, NOT_WHITESPACE);
                            every.pollInterval = parseInterval(consumeUntil(tokens, /[,\[\s]/));
                            consumeUntil(tokens, NOT_WHITESPACE);
                            var eventFilter = maybeGenerateConditional(elt, tokens, "event");
                            if (eventFilter) {
                                every.eventFilter = eventFilter;
                            }
                            triggerSpecs.push(every);
                        } else if (trigger.indexOf("sse:") === 0) {
                            triggerSpecs.push({trigger: 'sse', sseEvent: trigger.substr(4)});
                        } else {
                            var triggerSpec = {trigger: trigger};
                            var eventFilter = maybeGenerateConditional(elt, tokens, "event");
                            if (eventFilter) {
                                triggerSpec.eventFilter = eventFilter;
                            }
                            while (tokens.length > 0 && tokens[0] !== ",") {
                                consumeUntil(tokens, NOT_WHITESPACE)
                                var token = tokens.shift();
                                if (token === "changed") {
                                    triggerSpec.changed = true;
                                } else if (token === "once") {
                                    triggerSpec.once = true;
                                } else if (token === "consume") {
                                    triggerSpec.consume = true;
                                } else if (token === "delay" && tokens[0] === ":") {
                                    tokens.shift();
                                    triggerSpec.delay = parseInterval(consumeUntil(tokens, WHITESPACE_OR_COMMA));
                                } else if (token === "from" && tokens[0] === ":") {
                                    tokens.shift();
                                    var from_arg = consumeUntil(tokens, WHITESPACE_OR_COMMA);
                                    if (from_arg === "closest" || from_arg === "find" || from_arg === "next" || from_arg === "previous") {
                                        tokens.shift();
                                        from_arg +=
                                            " " +
                                            consumeUntil(
                                                tokens,
                                                WHITESPACE_OR_COMMA
                                            );
                                    }
                                    triggerSpec.from = from_arg;
                                } else if (token === "target" && tokens[0] === ":") {
                                    tokens.shift();
                                    triggerSpec.target = consumeUntil(tokens, WHITESPACE_OR_COMMA);
                                } else if (token === "throttle" && tokens[0] === ":") {
                                    tokens.shift();
                                    triggerSpec.throttle = parseInterval(consumeUntil(tokens, WHITESPACE_OR_COMMA));
                                } else if (token === "queue" && tokens[0] === ":") {
                                    tokens.shift();
                                    triggerSpec.queue = consumeUntil(tokens, WHITESPACE_OR_COMMA);
                                } else if ((token === "root" || token === "threshold") && tokens[0] === ":") {
                                    tokens.shift();
                                    triggerSpec[token] = consumeUntil(tokens, WHITESPACE_OR_COMMA);
                                } else {
                                    triggerErrorEvent(elt, "htmx:syntax:error", {token:tokens.shift()});
                                }
                            }
                            triggerSpecs.push(triggerSpec);
                        }
                    }
                    if (tokens.length === initialLength) {
                        triggerErrorEvent(elt, "htmx:syntax:error", {token:tokens.shift()});
                    }
                    consumeUntil(tokens, NOT_WHITESPACE);
                } while (tokens[0] === "," && tokens.shift())
            }

            if (triggerSpecs.length > 0) {
                return triggerSpecs;
            } else if (matches(elt, 'form')) {
                return [{trigger: 'submit'}];
            } else if (matches(elt, 'input[type="button"]')){
                return [{trigger: 'click'}];
            } else if (matches(elt, INPUT_SELECTOR)) {
                return [{trigger: 'change'}];
            } else {
                return [{trigger: 'click'}];
            }
        }

        function cancelPolling(elt) {
            getInternalData(elt).cancelled = true;
        }

        function processPolling(elt, handler, spec) {
            var nodeData = getInternalData(elt);
            nodeData.timeout = setTimeout(function () {
                if (bodyContains(elt) && nodeData.cancelled !== true) {
                    if (!maybeFilterEvent(spec, makeEvent('hx:poll:trigger', {triggerSpec:spec, target:elt}))) {
                        handler(elt);
                    }
                    processPolling(elt, handler, spec);
                }
            }, spec.pollInterval);
        }

        function isLocalLink(elt) {
            return location.hostname === elt.hostname &&
                getRawAttribute(elt,'href') &&
                getRawAttribute(elt,'href').indexOf("#") !== 0;
        }

        function boostElement(elt, nodeData, triggerSpecs) {
            if ((elt.tagName === "A" && isLocalLink(elt) && (elt.target === "" || elt.target === "_self")) || elt.tagName === "FORM") {
                nodeData.boosted = true;
                var verb, path;
                if (elt.tagName === "A") {
                    verb = "get";
                    path = getRawAttribute(elt, 'href');
                } else {
                    var rawAttribute = getRawAttribute(elt, "method");
                    verb = rawAttribute ? rawAttribute.toLowerCase() : "get";
                    if (verb === "get") {
                    }
                    path = getRawAttribute(elt, 'action');
                }
                triggerSpecs.forEach(function(triggerSpec) {
                    addEventListener(elt, function(elt, evt) {
                        issueAjaxRequest(verb, path, elt, evt)
                    }, nodeData, triggerSpec, true);
                });
            }
        }

        /**
         *
         * @param {Event} evt
         * @param {HTMLElement} elt
         * @returns
         */
        function shouldCancel(evt, elt) {
            if (evt.type === "submit" || evt.type === "click") {
                if (elt.tagName === "FORM") {
                    return true;
                }
                if (matches(elt, 'input[type="submit"], button') && closest(elt, 'form') !== null) {
                    return true;
                }
                if (elt.tagName === "A" && elt.href &&
                    (elt.getAttribute('href') === '#' || elt.getAttribute('href').indexOf("#") !== 0)) {
                    return true;
                }
            }
            return false;
        }

        function ignoreBoostedAnchorCtrlClick(elt, evt) {
            return getInternalData(elt).boosted && elt.tagName === "A" && evt.type === "click" && (evt.ctrlKey || evt.metaKey);
        }

        function maybeFilterEvent(triggerSpec, evt) {
            var eventFilter = triggerSpec.eventFilter;
            if(eventFilter){
                try {
                    return eventFilter(evt) !== true;
                } catch(e) {
                    triggerErrorEvent(getDocument().body, "htmx:eventFilter:error", {error: e, source:eventFilter.source});
                    return true;
                }
            }
            return false;
        }

        function addEventListener(elt, handler, nodeData, triggerSpec, explicitCancel) {
            var elementData = getInternalData(elt);
            var eltsToListenOn;
            if (triggerSpec.from) {
                eltsToListenOn = querySelectorAllExt(elt, triggerSpec.from);
            } else {
                eltsToListenOn = [elt];
            }
            // store the initial value of the element so we can tell if it changes
            if (triggerSpec.changed) {
                elementData.lastValue = elt.value;
            }
            forEach(eltsToListenOn, function (eltToListenOn) {
                var eventListener = function (evt) {
                    if (!bodyContains(elt)) {
                        eltToListenOn.removeEventListener(triggerSpec.trigger, eventListener);
                        return;
                    }
                    if (ignoreBoostedAnchorCtrlClick(elt, evt)) {
                        return;
                    }
                    if (explicitCancel || shouldCancel(evt, elt)) {
                        evt.preventDefault();
                    }
                    if (maybeFilterEvent(triggerSpec, evt)) {
                        return;
                    }
                    var eventData = getInternalData(evt);
                    eventData.triggerSpec = triggerSpec;
                    if (eventData.handledFor == null) {
                        eventData.handledFor = [];
                    }
                    if (eventData.handledFor.indexOf(elt) < 0) {
                        eventData.handledFor.push(elt);
                        if (triggerSpec.consume) {
                            evt.stopPropagation();
                        }
                        if (triggerSpec.target && evt.target) {
                            if (!matches(evt.target, triggerSpec.target)) {
                                return;
                            }
                        }
                        if (triggerSpec.once) {
                            if (elementData.triggeredOnce) {
                                return;
                            } else {
                                elementData.triggeredOnce = true;
                            }
                        }
                        if (triggerSpec.changed) {
                            if (elementData.lastValue === elt.value) {
                                return;
                            } else {
                                elementData.lastValue = elt.value;
                            }
                        }
                        if (elementData.delayed) {
                            clearTimeout(elementData.delayed);
                        }
                        if (elementData.throttle) {
                            return;
                        }

                        if (triggerSpec.throttle) {
                            if (!elementData.throttle) {
                                handler(elt, evt);
                                elementData.throttle = setTimeout(function () {
                                    elementData.throttle = null;
                                }, triggerSpec.throttle);
                            }
                        } else if (triggerSpec.delay) {
                            elementData.delayed = setTimeout(function() { handler(elt, evt) }, triggerSpec.delay);
                        } else {
                            handler(elt, evt);
                        }
                    }
                };
                if (nodeData.listenerInfos == null) {
                    nodeData.listenerInfos = [];
                }
                nodeData.listenerInfos.push({
                    trigger: triggerSpec.trigger,
                    listener: eventListener,
                    on: eltToListenOn
                })
                eltToListenOn.addEventListener(triggerSpec.trigger, eventListener);
            });
        }

        var windowIsScrolling = false // used by initScrollHandler
        var scrollHandler = null;
        function initScrollHandler() {
            if (!scrollHandler) {
                scrollHandler = function() {
                    windowIsScrolling = true
                };
                window.addEventListener("scroll", scrollHandler)
                setInterval(function() {
                    if (windowIsScrolling) {
                        windowIsScrolling = false;
                        forEach(getDocument().querySelectorAll("[hx-trigger='revealed'],[data-hx-trigger='revealed']"), function (elt) {
                            maybeReveal(elt);
                        })
                    }
                }, 200);
            }
        }

        function maybeReveal(elt) {
            if (!hasAttribute(elt,'data-hx-revealed') && isScrolledIntoView(elt)) {
                elt.setAttribute('data-hx-revealed', 'true');
                var nodeData = getInternalData(elt);
                if (nodeData.initHash) {
                    triggerEvent(elt, 'revealed');
                } else {
                    // if the node isn't initialized, wait for it before triggering the request
                    elt.addEventListener("htmx:afterProcessNode", function(evt) { triggerEvent(elt, 'revealed') }, {once: true});
                }
            }
        }

        //====================================================================
        // Web Sockets
        //====================================================================

        function processWebSocketInfo(elt, nodeData, info) {
            var values = splitOnWhitespace(info);
            for (var i = 0; i < values.length; i++) {
                var value = values[i].split(/:(.+)/);
                if (value[0] === "connect") {
                    ensureWebSocket(elt, value[1], 0);
                }
                if (value[0] === "send") {
                    processWebSocketSend(elt);
                }
            }
        }

        function ensureWebSocket(elt, wssSource, retryCount) {
            if (!bodyContains(elt)) {
                return;  // stop ensuring websocket connection when socket bearing element ceases to exist
            }

            if (wssSource.indexOf("/") == 0) {  // complete absolute paths only
                var base_part = location.hostname + (location.port ? ':'+location.port: '');
                if (location.protocol == 'https:') {
                    wssSource = "wss://" + base_part + wssSource;
                } else if (location.protocol == 'http:') {
                    wssSource = "ws://" + base_part + wssSource;
                }
            }
            var socket = htmx.createWebSocket(wssSource);
            socket.onerror = function (e) {
                triggerErrorEvent(elt, "htmx:wsError", {error:e, socket:socket});
                maybeCloseWebSocketSource(elt);
            };

            socket.onclose = function (e) {
                if ([1006, 1012, 1013].indexOf(e.code) >= 0) {  // Abnormal Closure/Service Restart/Try Again Later
                    var delay = getWebSocketReconnectDelay(retryCount);
                    setTimeout(function() {
                        ensureWebSocket(elt, wssSource, retryCount+1);  // creates a websocket with a new timeout
                    }, delay);
                }
            };
            socket.onopen = function (e) {
                retryCount = 0;
            }

            getInternalData(elt).webSocket = socket;
            socket.addEventListener('message', function (event) {
                if (maybeCloseWebSocketSource(elt)) {
                    return;
                }

                var response = event.data;
                withExtensions(elt, function(extension){
                    response = extension.transformResponse(response, null, elt);
                });

                var settleInfo = makeSettleInfo(elt);
                var fragment = makeFragment(response);
                var children = toArray(fragment.children);
                for (var i = 0; i < children.length; i++) {
                    var child = children[i];
                    oobSwap(getAttributeValue(child, "hx-swap-oob") || "true", child, settleInfo);
                }

                settleImmediately(settleInfo.tasks);
            });
        }

        function maybeCloseWebSocketSource(elt) {
            if (!bodyContains(elt)) {
                getInternalData(elt).webSocket.close();
                return true;
            }
        }

        function processWebSocketSend(elt) {
            var webSocketSourceElt = getClosestMatch(elt, function (parent) {
                return getInternalData(parent).webSocket != null;
            });
            if (webSocketSourceElt) {
                elt.addEventListener(getTriggerSpecs(elt)[0].trigger, function (evt) {
                    var webSocket = getInternalData(webSocketSourceElt).webSocket;
                    var headers = getHeaders(elt, webSocketSourceElt);
                    var results = getInputValues(elt, 'post');
                    var errors = results.errors;
                    var rawParameters = results.values;
                    var expressionVars = getExpressionVars(elt);
                    var allParameters = mergeObjects(rawParameters, expressionVars);
                    var filteredParameters = filterValues(allParameters, elt);
                    filteredParameters['HEADERS'] = headers;
                    if (errors && errors.length > 0) {
                        triggerEvent(elt, 'htmx:validation:halted', errors);
                        return;
                    }
                    webSocket.send(JSON.stringify(filteredParameters));
                    if(shouldCancel(evt, elt)){
                        evt.preventDefault();
                    }
                });
            } else {
                triggerErrorEvent(elt, "htmx:noWebSocketSourceError");
            }
        }

        function getWebSocketReconnectDelay(retryCount) {
            var delay = htmx.config.wsReconnectDelay;
            if (typeof delay === 'function') {
                // @ts-ignore
                return delay(retryCount);
            }
            if (delay === 'full-jitter') {
                var exp = Math.min(retryCount, 6);
                var maxDelay = 1000 * Math.pow(2, exp);
                return maxDelay * Math.random();
            }
            logError('htmx.config.wsReconnectDelay must either be a function or the string "full-jitter"');
        }

        //====================================================================
        // Server Sent Events
        //====================================================================

        function processSSEInfo(elt, nodeData, info) {
            var values = splitOnWhitespace(info);
            for (var i = 0; i < values.length; i++) {
                var value = values[i].split(/:(.+)/);
                if (value[0] === "connect") {
                    processSSESource(elt, value[1]);
                }

                if ((value[0] === "swap")) {
                    processSSESwap(elt, value[1])
                }
            }
        }

        function processSSESource(elt, sseSrc) {
            var source = htmx.createEventSource(sseSrc);
            source.onerror = function (e) {
                triggerErrorEvent(elt, "htmx:sseError", {error:e, source:source});
                maybeCloseSSESource(elt);
            };
            getInternalData(elt).sseEventSource = source;
        }

        function processSSESwap(elt, sseEventName) {
            var sseSourceElt = getClosestMatch(elt, hasEventSource);
            if (sseSourceElt) {
                var sseEventSource = getInternalData(sseSourceElt).sseEventSource;
                var sseListener = function (event) {
                    if (maybeCloseSSESource(sseSourceElt)) {
                        sseEventSource.removeEventListener(sseEventName, sseListener);
                        return;
                    }

                    ///////////////////////////
                    // TODO: merge this code with AJAX and WebSockets code in the future.

                    var response = event.data;
                    withExtensions(elt, function(extension){
                        response = extension.transformResponse(response, null, elt);
                    });

                    var swapSpec = getSwapSpecification(elt)
                    var target = getTarget(elt)
                    var settleInfo = makeSettleInfo(elt);

                    selectAndSwap(swapSpec.swapStyle, elt, target, response, settleInfo)
                    settleImmediately(settleInfo.tasks)
                    triggerEvent(elt, "htmx:sseMessage", event)
                };

                getInternalData(elt).sseListener = sseListener;
                sseEventSource.addEventListener(sseEventName, sseListener);
            } else {
                triggerErrorEvent(elt, "htmx:noSSESourceError");
            }
        }

        function processSSETrigger(elt, handler, sseEventName) {
            var sseSourceElt = getClosestMatch(elt, hasEventSource);
            if (sseSourceElt) {
                var sseEventSource = getInternalData(sseSourceElt).sseEventSource;
                var sseListener = function () {
                    if (!maybeCloseSSESource(sseSourceElt)) {
                        if (bodyContains(elt)) {
                            handler(elt);
                        } else {
                            sseEventSource.removeEventListener(sseEventName, sseListener);
                        }
                    }
                };
                getInternalData(elt).sseListener = sseListener;
                sseEventSource.addEventListener(sseEventName, sseListener);
            } else {
                triggerErrorEvent(elt, "htmx:noSSESourceError");
            }
        }

        function maybeCloseSSESource(elt) {
            if (!bodyContains(elt)) {
                getInternalData(elt).sseEventSource.close();
                return true;
            }
        }

        function hasEventSource(node) {
            return getInternalData(node).sseEventSource != null;
        }

        //====================================================================

        function loadImmediately(elt, handler, nodeData, delay) {
            var load = function(){
                if (!nodeData.loaded) {
                    nodeData.loaded = true;
                    handler(elt);
                }
            }
            if (delay) {
                setTimeout(load, delay);
            } else {
                load();
            }
        }

        function processVerbs(elt, nodeData, triggerSpecs) {
            var explicitAction = false;
            forEach(VERBS, function (verb) {
                if (hasAttribute(elt,'hx-' + verb)) {
                    var path = getAttributeValue(elt, 'hx-' + verb);
                    explicitAction = true;
                    nodeData.path = path;
                    nodeData.verb = verb;
                    triggerSpecs.forEach(function(triggerSpec) {
                        addTriggerHandler(elt, triggerSpec, nodeData, function (elt, evt) {
                            issueAjaxRequest(verb, path, elt, evt)
                        })
                    });
                }
            });
            return explicitAction;
        }

        function addTriggerHandler(elt, triggerSpec, nodeData, handler) {
            if (triggerSpec.sseEvent) {
                processSSETrigger(elt, handler, triggerSpec.sseEvent);
            } else if (triggerSpec.trigger === "revealed") {
                initScrollHandler();
                addEventListener(elt, handler, nodeData, triggerSpec);
                maybeReveal(elt);
            } else if (triggerSpec.trigger === "intersect") {
                var observerOptions = {};
                if (triggerSpec.root) {
                    observerOptions.root = querySelectorExt(elt, triggerSpec.root)
                }
                if (triggerSpec.threshold) {
                    observerOptions.threshold = parseFloat(triggerSpec.threshold);
                }
                var observer = new IntersectionObserver(function (entries) {
                    for (var i = 0; i < entries.length; i++) {
                        var entry = entries[i];
                        if (entry.isIntersecting) {
                            triggerEvent(elt, "intersect");
                            break;
                        }
                    }
                }, observerOptions);
                observer.observe(elt);
                addEventListener(elt, handler, nodeData, triggerSpec);
            } else if (triggerSpec.trigger === "load") {
                if (!maybeFilterEvent(triggerSpec, makeEvent("load", {elt:elt}))) {
                                loadImmediately(elt, handler, nodeData, triggerSpec.delay);
                            }
            } else if (triggerSpec.pollInterval) {
                nodeData.polling = true;
                processPolling(elt, handler, triggerSpec);
            } else {
                addEventListener(elt, handler, nodeData, triggerSpec);
            }
        }

        function evalScript(script) {
            if (script.type === "text/javascript" || script.type === "module" || script.type === "") {
                var newScript = getDocument().createElement("script");
                forEach(script.attributes, function (attr) {
                    newScript.setAttribute(attr.name, attr.value);
                });
                newScript.textContent = script.textContent;
                newScript.async = false;
                if (htmx.config.inlineScriptNonce) {
                    newScript.nonce = htmx.config.inlineScriptNonce;
                }
                var parent = script.parentElement;

                try {
                    parent.insertBefore(newScript, script);
                } catch (e) {
                    logError(e);
                } finally {
                    // remove old script element, but only if it is still in DOM
                    if (script.parentElement) {
                        script.parentElement.removeChild(script);
                    }
                }
            }
        }

        function processScripts(elt) {
            if (matches(elt, "script")) {
                evalScript(elt);
            }
            forEach(findAll(elt, "script"), function (script) {
                evalScript(script);
            });
        }

        function hasChanceOfBeingBoosted() {
            return document.querySelector("[hx-boost], [data-hx-boost]");
        }

        function findElementsToProcess(elt) {
            if (elt.querySelectorAll) {
                var boostedElts = hasChanceOfBeingBoosted() ? ", a, form" : "";
                var results = elt.querySelectorAll(VERB_SELECTOR + boostedElts + ", [hx-sse], [data-hx-sse], [hx-ws]," +
                    " [data-hx-ws], [hx-ext], [data-hx-ext]");
                return results;
            } else {
                return [];
            }
        }

        function initButtonTracking(form){
            var maybeSetLastButtonClicked = function(evt){
                var elt = closest(evt.target, "button, input[type='submit']");
                if (elt !== null) {
                    var internalData = getInternalData(form);
                    internalData.lastButtonClicked = elt;
                }
            };

            // need to handle both click and focus in:
            //   focusin - in case someone tabs in to a button and hits the space bar
            //   click - on OSX buttons do not focus on click see https://bugs.webkit.org/show_bug.cgi?id=13724

            form.addEventListener('click', maybeSetLastButtonClicked)
            form.addEventListener('focusin', maybeSetLastButtonClicked)
            form.addEventListener('focusout', function(evt){
                var internalData = getInternalData(form);
                internalData.lastButtonClicked = null;
            })
        }

        function initNode(elt) {
            if (elt.closest && elt.closest(htmx.config.disableSelector)) {
                return;
            }
            var nodeData = getInternalData(elt);
            if (nodeData.initHash !== attributeHash(elt)) {

                nodeData.initHash = attributeHash(elt);

                // clean up any previously processed info
                deInitNode(elt);

                triggerEvent(elt, "htmx:beforeProcessNode")

                if (elt.value) {
                    nodeData.lastValue = elt.value;
                }

                var triggerSpecs = getTriggerSpecs(elt);
                var explicitAction = processVerbs(elt, nodeData, triggerSpecs);

                if (!explicitAction && getClosestAttributeValue(elt, "hx-boost") === "true") {
                    boostElement(elt, nodeData, triggerSpecs);
                }

                if (elt.tagName === "FORM") {
                    initButtonTracking(elt);
                }

                var sseInfo = getAttributeValue(elt, 'hx-sse');
                if (sseInfo) {
                    processSSEInfo(elt, nodeData, sseInfo);
                }

                var wsInfo = getAttributeValue(elt, 'hx-ws');
                if (wsInfo) {
                    processWebSocketInfo(elt, nodeData, wsInfo);
                }
                triggerEvent(elt, "htmx:afterProcessNode");
            }
        }

        function processNode(elt) {
            elt = resolveTarget(elt);
            initNode(elt);
            forEach(findElementsToProcess(elt), function(child) { initNode(child) });
        }

        //====================================================================
        // Event/Log Support
        //====================================================================

        function kebabEventName(str) {
            return str.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase();
        }

        function makeEvent(eventName, detail) {
            var evt;
            if (window.CustomEvent && typeof window.CustomEvent === 'function') {
                evt = new CustomEvent(eventName, {bubbles: true, cancelable: true, detail: detail});
            } else {
                evt = getDocument().createEvent('CustomEvent');
                evt.initCustomEvent(eventName, true, true, detail);
            }
            return evt;
        }

        function triggerErrorEvent(elt, eventName, detail) {
            triggerEvent(elt, eventName, mergeObjects({error:eventName}, detail));
        }

        function ignoreEventForLogging(eventName) {
            return eventName === "htmx:afterProcessNode"
        }

        /**
         * `withExtensions` locates all active extensions for a provided element, then
         * executes the provided function using each of the active extensions.  It should
         * be called internally at every extendable execution point in htmx.
         *
         * @param {HTMLElement} elt
         * @param {(extension:import("./htmx").HtmxExtension) => void} toDo
         * @returns void
         */
        function withExtensions(elt, toDo) {
            forEach(getExtensions(elt), function(extension){
                try {
                    toDo(extension);
                } catch (e) {
                    logError(e);
                }
            });
        }

        function logError(msg) {
            if(console.error) {
                console.error(msg);
            } else if (console.log) {
                console.log("ERROR: ", msg);
            }
        }

        function triggerEvent(elt, eventName, detail) {
            elt = resolveTarget(elt);
            if (detail == null) {
                detail = {};
            }
            detail["elt"] = elt;
            var event = makeEvent(eventName, detail);
            if (htmx.logger && !ignoreEventForLogging(eventName)) {
                htmx.logger(elt, eventName, detail);
            }
            if (detail.error) {
                logError(detail.error);
                triggerEvent(elt, "htmx:error", {errorInfo:detail})
            }
            var eventResult = elt.dispatchEvent(event);
            var kebabName = kebabEventName(eventName);
            if (eventResult && kebabName !== eventName) {
                var kebabedEvent = makeEvent(kebabName, event.detail);
                eventResult = eventResult && elt.dispatchEvent(kebabedEvent)
            }
            withExtensions(elt, function (extension) {
                eventResult = eventResult && (extension.onEvent(eventName, event) !== false)
            });
            return eventResult;
        }

        //====================================================================
        // History Support
        //====================================================================
        var currentPathForHistory = location.pathname+location.search;

        function getHistoryElement() {
            var historyElt = getDocument().querySelector('[hx-history-elt],[data-hx-history-elt]');
            return historyElt || getDocument().body;
        }

        function saveToHistoryCache(url, content, title, scroll) {
            if (!canAccessLocalStorage()) {
                return;
            }

            var historyCache = parseJSON(localStorage.getItem("htmx-history-cache")) || [];
            for (var i = 0; i < historyCache.length; i++) {
                if (historyCache[i].url === url) {
                    historyCache.splice(i, 1);
                    break;
                }
            }
            var newHistoryItem = {url:url, content: content, title:title, scroll:scroll};
            triggerEvent(getDocument().body, "htmx:historyItemCreated", {item:newHistoryItem, cache: historyCache})
            historyCache.push(newHistoryItem)
            while (historyCache.length > htmx.config.historyCacheSize) {
                historyCache.shift();
            }
            while(historyCache.length > 0){
                try {
                    localStorage.setItem("htmx-history-cache", JSON.stringify(historyCache));
                    break;
                } catch (e) {
                    triggerErrorEvent(getDocument().body, "htmx:historyCacheError", {cause:e, cache: historyCache})
                    historyCache.shift(); // shrink the cache and retry
                }
            }
        }

        function getCachedHistory(url) {
            if (!canAccessLocalStorage()) {
                return null;
            }

            var historyCache = parseJSON(localStorage.getItem("htmx-history-cache")) || [];
            for (var i = 0; i < historyCache.length; i++) {
                if (historyCache[i].url === url) {
                    return historyCache[i];
                }
            }
            return null;
        }

        function cleanInnerHtmlForHistory(elt) {
            var className = htmx.config.requestClass;
            var clone = elt.cloneNode(true);
            forEach(findAll(clone, "." + className), function(child){
                removeClassFromElement(child, className);
            });
            return clone.innerHTML;
        }

        function saveCurrentPageToHistory() {
            var elt = getHistoryElement();
            var path = currentPathForHistory || location.pathname+location.search;

            // Allow history snapshot feature to be disabled where hx-history="false"
            // is present *anywhere* in the current document we're about to save,
            // so we can prevent privileged data entering the cache.
            // The page will still be reachable as a history entry, but htmx will fetch it
            // live from the server onpopstate rather than look in the localStorage cache
            var disableHistoryCache = getDocument().querySelector('[hx-history="false" i],[data-hx-history="false" i]');
            if (!disableHistoryCache) {
                triggerEvent(getDocument().body, "htmx:beforeHistorySave", {path: path, historyElt: elt});
                saveToHistoryCache(path, cleanInnerHtmlForHistory(elt), getDocument().title, window.scrollY);
            }

            if (htmx.config.historyEnabled) history.replaceState({htmx: true}, getDocument().title, window.location.href);
        }

        function pushUrlIntoHistory(path) {
            // remove the cache buster parameter, if any
            if (htmx.config.getCacheBusterParam) {
                path = path.replace(/org\.htmx\.cache-buster=[^&]*&?/, '')
                if (path.endsWith('&') || path.endsWith("?")) {
                    path = path.slice(0, -1);
                }
            }
            if(htmx.config.historyEnabled) {
                history.pushState({htmx:true}, "", path);
            }
            currentPathForHistory = path;
        }

        function replaceUrlInHistory(path) {
            if(htmx.config.historyEnabled)  history.replaceState({htmx:true}, "", path);
            currentPathForHistory = path;
        }

        function settleImmediately(tasks) {
            forEach(tasks, function (task) {
                task.call();
            });
        }

        function loadHistoryFromServer(path) {
            var request = new XMLHttpRequest();
            var details = {path: path, xhr:request};
            triggerEvent(getDocument().body, "htmx:historyCacheMiss", details);
            request.open('GET', path, true);
            request.setRequestHeader("HX-History-Restore-Request", "true");
            request.onload = function () {
                if (this.status >= 200 && this.status < 400) {
                    triggerEvent(getDocument().body, "htmx:historyCacheMissLoad", details);
                    var fragment = makeFragment(this.response);
                    // @ts-ignore
                    fragment = fragment.querySelector('[hx-history-elt],[data-hx-history-elt]') || fragment;
                    var historyElement = getHistoryElement();
                    var settleInfo = makeSettleInfo(historyElement);
                    var title = findTitle(this.response);
                    if (title) {
                        var titleElt = find("title");
                        if (titleElt) {
                            titleElt.innerHTML = title;
                        } else {
                            window.document.title = title;
                        }
                    }
                    // @ts-ignore
                    swapInnerHTML(historyElement, fragment, settleInfo)
                    settleImmediately(settleInfo.tasks);
                    currentPathForHistory = path;
                    triggerEvent(getDocument().body, "htmx:historyRestore", {path: path, cacheMiss:true, serverResponse:this.response});
                } else {
                    triggerErrorEvent(getDocument().body, "htmx:historyCacheMissLoadError", details);
                }
            };
            request.send();
        }

        function restoreHistory(path) {
            saveCurrentPageToHistory();
            path = path || location.pathname+location.search;
            var cached = getCachedHistory(path);
            if (cached) {
                var fragment = makeFragment(cached.content);
                var historyElement = getHistoryElement();
                var settleInfo = makeSettleInfo(historyElement);
                swapInnerHTML(historyElement, fragment, settleInfo)
                settleImmediately(settleInfo.tasks);
                document.title = cached.title;
                window.scrollTo(0, cached.scroll);
                currentPathForHistory = path;
                triggerEvent(getDocument().body, "htmx:historyRestore", {path:path, item:cached});
            } else {
                if (htmx.config.refreshOnHistoryMiss) {

                    // @ts-ignore: optional parameter in reload() function throws error
                    window.location.reload(true);
                } else {
                    loadHistoryFromServer(path);
                }
            }
        }

        function addRequestIndicatorClasses(elt) {
            var indicators = findAttributeTargets(elt, 'hx-indicator');
            if (indicators == null) {
                indicators = [elt];
            }
            forEach(indicators, function (ic) {
                var internalData = getInternalData(ic);
                internalData.requestCount = (internalData.requestCount || 0) + 1;
                ic.classList["add"].call(ic.classList, htmx.config.requestClass);
            });
            return indicators;
        }

        function removeRequestIndicatorClasses(indicators) {
            forEach(indicators, function (ic) {
                var internalData = getInternalData(ic);
                internalData.requestCount = (internalData.requestCount || 0) - 1;
                if (internalData.requestCount === 0) {
                    ic.classList["remove"].call(ic.classList, htmx.config.requestClass);
                }
            });
        }

        //====================================================================
        // Input Value Processing
        //====================================================================

        function haveSeenNode(processed, elt) {
            for (var i = 0; i < processed.length; i++) {
                var node = processed[i];
                if (node.isSameNode(elt)) {
                    return true;
                }
            }
            return false;
        }

        function shouldInclude(elt) {
            if(elt.name === "" || elt.name == null || elt.disabled) {
                return false;
            }
            // ignore "submitter" types (see jQuery src/serialize.js)
            if (elt.type === "button" || elt.type === "submit" || elt.tagName === "image" || elt.tagName === "reset" || elt.tagName === "file" ) {
                return false;
            }
            if (elt.type === "checkbox" || elt.type === "radio" ) {
                return elt.checked;
            }
            return true;
        }

        function processInputValue(processed, values, errors, elt, validate) {
            if (elt == null || haveSeenNode(processed, elt)) {
                return;
            } else {
                processed.push(elt);
            }
            if (shouldInclude(elt)) {
                var name = getRawAttribute(elt,"name");
                var value = elt.value;
                if (elt.multiple) {
                    value = toArray(elt.querySelectorAll("option:checked")).map(function (e) { return e.value });
                }
                // include file inputs
                if (elt.files) {
                    value = toArray(elt.files);
                }
                // This is a little ugly because both the current value of the named value in the form
                // and the new value could be arrays, so we have to handle all four cases :/
                if (name != null && value != null) {
                    var current = values[name];
                    if (current !== undefined) {
                        if (Array.isArray(current)) {
                            if (Array.isArray(value)) {
                                values[name] = current.concat(value);
                            } else {
                                current.push(value);
                            }
                        } else {
                            if (Array.isArray(value)) {
                                values[name] = [current].concat(value);
                            } else {
                                values[name] = [current, value];
                            }
                        }
                    } else {
                        values[name] = value;
                    }
                }
                if (validate) {
                    validateElement(elt, errors);
                }
            }
            if (matches(elt, 'form')) {
                var inputs = elt.elements;
                forEach(inputs, function(input) {
                    processInputValue(processed, values, errors, input, validate);
                });
            }
        }

        function validateElement(element, errors) {
            if (element.willValidate) {
                triggerEvent(element, "htmx:validation:validate")
                if (!element.checkValidity()) {
                    errors.push({elt: element, message:element.validationMessage, validity:element.validity});
                    triggerEvent(element, "htmx:validation:failed", {message:element.validationMessage, validity:element.validity})
                }
            }
        }

        /**
         * @param {HTMLElement} elt
         * @param {string} verb
         */
        function getInputValues(elt, verb) {
            var processed = [];
            var values = {};
            var formValues = {};
            var errors = [];
            var internalData = getInternalData(elt);

            // only validate when form is directly submitted and novalidate or formnovalidate are not set
            // or if the element has an explicit hx-validate="true" on it
            var validate = (matches(elt, 'form') && elt.noValidate !== true) || getAttributeValue(elt, "hx-validate") === "true";
            if (internalData.lastButtonClicked) {
                validate = validate && internalData.lastButtonClicked.formNoValidate !== true;
            }

            // for a non-GET include the closest form
            if (verb !== 'get') {
                processInputValue(processed, formValues, errors, closest(elt, 'form'), validate);
            }

            // include the element itself
            processInputValue(processed, values, errors, elt, validate);

            // if a button or submit was clicked last, include its value
            if (internalData.lastButtonClicked) {
                var name = getRawAttribute(internalData.lastButtonClicked,"name");
                if (name) {
                    values[name] = internalData.lastButtonClicked.value;
                }
            }

            // include any explicit includes
            var includes = findAttributeTargets(elt, "hx-include");
            forEach(includes, function(node) {
                processInputValue(processed, values, errors, node, validate);
                // if a non-form is included, include any input values within it
                if (!matches(node, 'form')) {
                    forEach(node.querySelectorAll(INPUT_SELECTOR), function (descendant) {
                        processInputValue(processed, values, errors, descendant, validate);
                    })
                }
            });

            // form values take precedence, overriding the regular values
            values = mergeObjects(values, formValues);

            return {errors:errors, values:values};
        }

        function appendParam(returnStr, name, realValue) {
            if (returnStr !== "") {
                returnStr += "&";
            }
            if (String(realValue) === "[object Object]") {
                realValue = JSON.stringify(realValue);
            }
            var s = encodeURIComponent(realValue);
            returnStr += encodeURIComponent(name) + "=" + s;
            return returnStr;
        }

        function urlEncode(values) {
            var returnStr = "";
            for (var name in values) {
                if (values.hasOwnProperty(name)) {
                    var value = values[name];
                    if (Array.isArray(value)) {
                        forEach(value, function(v) {
                            returnStr = appendParam(returnStr, name, v);
                        });
                    } else {
                        returnStr = appendParam(returnStr, name, value);
                    }
                }
            }
            return returnStr;
        }

        function makeFormData(values) {
            var formData = new FormData();
            for (var name in values) {
                if (values.hasOwnProperty(name)) {
                    var value = values[name];
                    if (Array.isArray(value)) {
                        forEach(value, function(v) {
                            formData.append(name, v);
                        });
                    } else {
                        formData.append(name, value);
                    }
                }
            }
            return formData;
        }

        //====================================================================
        // Ajax
        //====================================================================

        /**
         * @param {HTMLElement} elt
         * @param {HTMLElement} target
         * @param {string} prompt
         * @returns {Object} // TODO: Define/Improve HtmxHeaderSpecification
         */
        function getHeaders(elt, target, prompt) {
            var headers = {
                "HX-Request" : "true",
                "HX-Trigger" : getRawAttribute(elt, "id"),
                "HX-Trigger-Name" : getRawAttribute(elt, "name"),
                "HX-Target" : getAttributeValue(target, "id"),
                "HX-Current-URL" : getDocument().location.href,
            }
            getValuesForElement(elt, "hx-headers", false, headers)
            if (prompt !== undefined) {
                headers["HX-Prompt"] = prompt;
            }
            if (getInternalData(elt).boosted) {
                headers["HX-Boosted"] = "true";
            }
            return headers;
        }

        /**
         * filterValues takes an object containing form input values
         * and returns a new object that only contains keys that are
         * specified by the closest "hx-params" attribute
         * @param {Object} inputValues
         * @param {HTMLElement} elt
         * @returns {Object}
         */
        function filterValues(inputValues, elt) {
            var paramsValue = getClosestAttributeValue(elt, "hx-params");
            if (paramsValue) {
                if (paramsValue === "none") {
                    return {};
                } else if (paramsValue === "*") {
                    return inputValues;
                } else if(paramsValue.indexOf("not ") === 0) {
                    forEach(paramsValue.substr(4).split(","), function (name) {
                        name = name.trim();
                        delete inputValues[name];
                    });
                    return inputValues;
                } else {
                    var newValues = {}
                    forEach(paramsValue.split(","), function (name) {
                        name = name.trim();
                        newValues[name] = inputValues[name];
                    });
                    return newValues;
                }
            } else {
                return inputValues;
            }
        }

        function isAnchorLink(elt) {
          return getRawAttribute(elt, 'href') && getRawAttribute(elt, 'href').indexOf("#") >=0
        }

        /**
         *
         * @param {HTMLElement} elt
         * @param {string} swapInfoOverride
         * @returns {import("./htmx").HtmxSwapSpecification}
         */
        function getSwapSpecification(elt, swapInfoOverride) {
            var swapInfo = swapInfoOverride ? swapInfoOverride : getClosestAttributeValue(elt, "hx-swap");
            var swapSpec = {
                "swapStyle" : getInternalData(elt).boosted ? 'innerHTML' : htmx.config.defaultSwapStyle,
                "swapDelay" : htmx.config.defaultSwapDelay,
                "settleDelay" : htmx.config.defaultSettleDelay
            }
            if (getInternalData(elt).boosted && !isAnchorLink(elt)) {
              swapSpec["show"] = "top"
            }
            if (swapInfo) {
                var split = splitOnWhitespace(swapInfo);
                if (split.length > 0) {
                    swapSpec["swapStyle"] = split[0];
                    for (var i = 1; i < split.length; i++) {
                        var modifier = split[i];
                        if (modifier.indexOf("swap:") === 0) {
                            swapSpec["swapDelay"] = parseInterval(modifier.substr(5));
                        }
                        if (modifier.indexOf("settle:") === 0) {
                            swapSpec["settleDelay"] = parseInterval(modifier.substr(7));
                        }
                        if (modifier.indexOf("scroll:") === 0) {
                            var scrollSpec = modifier.substr(7);
                            var splitSpec = scrollSpec.split(":");
                            var scrollVal = splitSpec.pop();
                            var selectorVal = splitSpec.length > 0 ? splitSpec.join(":") : null;
                            swapSpec["scroll"] = scrollVal;
                            swapSpec["scrollTarget"] = selectorVal;
                        }
                        if (modifier.indexOf("show:") === 0) {
                            var showSpec = modifier.substr(5);
                            var splitSpec = showSpec.split(":");
                            var showVal = splitSpec.pop();
                            var selectorVal = splitSpec.length > 0 ? splitSpec.join(":") : null;
                            swapSpec["show"] = showVal;
                            swapSpec["showTarget"] = selectorVal;
                        }
                        if (modifier.indexOf("focus-scroll:") === 0) {
                            var focusScrollVal = modifier.substr("focus-scroll:".length);
                            swapSpec["focusScroll"] = focusScrollVal == "true";
                        }
                    }
                }
            }
            return swapSpec;
        }

        function usesFormData(elt) {
            return getClosestAttributeValue(elt, "hx-encoding") === "multipart/form-data" ||
                (matches(elt, "form") && getRawAttribute(elt, 'enctype') === "multipart/form-data");
        }

        function encodeParamsForBody(xhr, elt, filteredParameters) {
            var encodedParameters = null;
            withExtensions(elt, function (extension) {
                if (encodedParameters == null) {
                    encodedParameters = extension.encodeParameters(xhr, filteredParameters, elt);
                }
            });
            if (encodedParameters != null) {
                return encodedParameters;
            } else {
                if (usesFormData(elt)) {
                    return makeFormData(filteredParameters);
                } else {
                    return urlEncode(filteredParameters);
                }
            }
        }

        /**
         *
         * @param {Element} target
         * @returns {import("./htmx").HtmxSettleInfo}
         */
        function makeSettleInfo(target) {
            return {tasks: [], elts: [target]};
        }

        function updateScrollState(content, swapSpec) {
            var first = content[0];
            var last = content[content.length - 1];
            if (swapSpec.scroll) {
                var target = null;
                if (swapSpec.scrollTarget) {
                    target = querySelectorExt(first, swapSpec.scrollTarget);
                }
                if (swapSpec.scroll === "top" && (first || target)) {
                    target = target || first;
                    target.scrollTop = 0;
                }
                if (swapSpec.scroll === "bottom" && (last || target)) {
                    target = target || last;
                    target.scrollTop = target.scrollHeight;
                }
            }
            if (swapSpec.show) {
                var target = null;
                if (swapSpec.showTarget) {
                    var targetStr = swapSpec.showTarget;
                    if (swapSpec.showTarget === "window") {
                        targetStr = "body";
                    }
                    target = querySelectorExt(first, targetStr);
                }
                if (swapSpec.show === "top" && (first || target)) {
                    target = target || first;
                    target.scrollIntoView({block:'start', behavior: htmx.config.scrollBehavior});
                }
                if (swapSpec.show === "bottom" && (last || target)) {
                    target = target || last;
                    target.scrollIntoView({block:'end', behavior: htmx.config.scrollBehavior});
                }
            }
        }

        /**
         * @param {HTMLElement} elt
         * @param {string} attr
         * @param {boolean=} evalAsDefault
         * @param {Object=} values
         * @returns {Object}
         */
        function getValuesForElement(elt, attr, evalAsDefault, values) {
            if (values == null) {
                values = {};
            }
            if (elt == null) {
                return values;
            }
            var attributeValue = getAttributeValue(elt, attr);
            if (attributeValue) {
                var str = attributeValue.trim();
                var evaluateValue = evalAsDefault;
                if (str === "unset") {
                    return null;
                }
                if (str.indexOf("javascript:") === 0) {
                    str = str.substr(11);
                    evaluateValue = true;
                } else if (str.indexOf("js:") === 0) {
                    str = str.substr(3);
                    evaluateValue = true;
                }
                if (str.indexOf('{') !== 0) {
                    str = "{" + str + "}";
                }
                var varsValues;
                if (evaluateValue) {
                    varsValues = maybeEval(elt,function () {return Function("return (" + str + ")")();}, {});
                } else {
                    varsValues = parseJSON(str);
                }
                for (var key in varsValues) {
                    if (varsValues.hasOwnProperty(key)) {
                        if (values[key] == null) {
                            values[key] = varsValues[key];
                        }
                    }
                }
            }
            return getValuesForElement(parentElt(elt), attr, evalAsDefault, values);
        }

        function maybeEval(elt, toEval, defaultVal) {
            if (htmx.config.allowEval) {
                return toEval();
            } else {
                triggerErrorEvent(elt, 'htmx:evalDisallowedError');
                return defaultVal;
            }
        }

        /**
         * @param {HTMLElement} elt
         * @param {*} expressionVars
         * @returns
         */
        function getHXVarsForElement(elt, expressionVars) {
            return getValuesForElement(elt, "hx-vars", true, expressionVars);
        }

        /**
         * @param {HTMLElement} elt
         * @param {*} expressionVars
         * @returns
         */
        function getHXValsForElement(elt, expressionVars) {
            return getValuesForElement(elt, "hx-vals", false, expressionVars);
        }

        /**
         * @param {HTMLElement} elt
         * @returns {Object}
         */
        function getExpressionVars(elt) {
            return mergeObjects(getHXVarsForElement(elt), getHXValsForElement(elt));
        }

        function safelySetHeaderValue(xhr, header, headerValue) {
            if (headerValue !== null) {
                try {
                    xhr.setRequestHeader(header, headerValue);
                } catch (e) {
                    // On an exception, try to set the header URI encoded instead
                    xhr.setRequestHeader(header, encodeURIComponent(headerValue));
                    xhr.setRequestHeader(header + "-URI-AutoEncoded", "true");
                }
            }
        }

        function getPathFromResponse(xhr) {
            // NB: IE11 does not support this stuff
            if (xhr.responseURL && typeof(URL) !== "undefined") {
                try {
                    var url = new URL(xhr.responseURL);
                    return url.pathname + url.search;
                } catch (e) {
                    triggerErrorEvent(getDocument().body, "htmx:badResponseUrl", {url: xhr.responseURL});
                }
            }
        }

        function hasHeader(xhr, regexp) {
            return xhr.getAllResponseHeaders().match(regexp);
        }

        function ajaxHelper(verb, path, context) {
            verb = verb.toLowerCase();
            if (context) {
                if (context instanceof Element || isType(context, 'String')) {
                    return issueAjaxRequest(verb, path, null, null, {
                        targetOverride: resolveTarget(context),
                        returnPromise: true
                    });
                } else {
                    return issueAjaxRequest(verb, path, resolveTarget(context.source), context.event,
                        {
                            handler : context.handler,
                            headers : context.headers,
                            values : context.values,
                            targetOverride: resolveTarget(context.target),
                            swapOverride: context.swap,
                            returnPromise: true
                        });
                }
            } else {
                return issueAjaxRequest(verb, path, null, null, {
                        returnPromise: true
                });
            }
        }

        function hierarchyForElt(elt) {
            var arr = [];
            while (elt) {
                arr.push(elt);
                elt = elt.parentElement;
            }
            return arr;
        }

        function issueAjaxRequest(verb, path, elt, event, etc, confirmed) {
            var resolve = null;
            var reject = null;
            etc = etc != null ? etc : {};
            if(etc.returnPromise && typeof Promise !== "undefined"){
                var promise = new Promise(function (_resolve, _reject) {
                    resolve = _resolve;
                    reject = _reject;
                });
            }
            if(elt == null) {
                elt = getDocument().body;
            }
            var responseHandler = etc.handler || handleAjaxResponse;

            if (!bodyContains(elt)) {
                return; // do not issue requests for elements removed from the DOM
            }
            var target = etc.targetOverride || getTarget(elt);
            if (target == null || target == DUMMY_ELT) {
                triggerErrorEvent(elt, 'htmx:targetError', {target: getAttributeValue(elt, "hx-target")});
                return;
            }

            // allow event-based confirmation w/ a callback
            if (!confirmed) {
                var issueRequest = function() {
                    return issueAjaxRequest(verb, path, elt, event, etc, true);
                }
                var confirmDetails = {target: target, elt: elt, path: path, verb: verb, triggeringEvent: event, etc: etc, issueRequest: issueRequest};
                if (triggerEvent(elt, 'htmx:confirm', confirmDetails) === false) {
                    return;
                }
            }

            var syncElt = elt;
            var eltData = getInternalData(elt);
            var syncStrategy = getClosestAttributeValue(elt, "hx-sync");
            var queueStrategy = null;
            var abortable = false;
            if (syncStrategy) {
                var syncStrings = syncStrategy.split(":");
                var selector = syncStrings[0].trim();
                if (selector === "this") {
                    syncElt = findThisElement(elt, 'hx-sync');
                } else {
                    syncElt = querySelectorExt(elt, selector);
                }
                // default to the drop strategy
                syncStrategy = (syncStrings[1] || 'drop').trim();
                eltData = getInternalData(syncElt);
                if (syncStrategy === "drop" && eltData.xhr && eltData.abortable !== true) {
                    return;
                } else if (syncStrategy === "abort") {
                    if (eltData.xhr) {
                        return;
                    } else {
                        abortable = true;
                    }
                } else if (syncStrategy === "replace") {
                    triggerEvent(syncElt, 'htmx:abort'); // abort the current request and continue
                } else if (syncStrategy.indexOf("queue") === 0) {
                    var queueStrArray = syncStrategy.split(" ");
                    queueStrategy = (queueStrArray[1] || "last").trim();
                }
            }

            if (eltData.xhr) {
                if (eltData.abortable) {
                    triggerEvent(syncElt, 'htmx:abort'); // abort the current request and continue
                } else {
                    if(queueStrategy == null){
                        if (event) {
                            var eventData = getInternalData(event);
                            if (eventData && eventData.triggerSpec && eventData.triggerSpec.queue) {
                                queueStrategy = eventData.triggerSpec.queue;
                            }
                        }
                        if (queueStrategy == null) {
                            queueStrategy = "last";
                        }
                    }
                    if (eltData.queuedRequests == null) {
                        eltData.queuedRequests = [];
                    }
                    if (queueStrategy === "first" && eltData.queuedRequests.length === 0) {
                        eltData.queuedRequests.push(function () {
                            issueAjaxRequest(verb, path, elt, event, etc)
                        });
                    } else if (queueStrategy === "all") {
                        eltData.queuedRequests.push(function () {
                            issueAjaxRequest(verb, path, elt, event, etc)
                        });
                    } else if (queueStrategy === "last") {
                        eltData.queuedRequests = []; // dump existing queue
                        eltData.queuedRequests.push(function () {
                            issueAjaxRequest(verb, path, elt, event, etc)
                        });
                    }
                    return;
                }
            }

            var xhr = new XMLHttpRequest();
            eltData.xhr = xhr;
            eltData.abortable = abortable;
            var endRequestLock = function(){
                eltData.xhr = null;
                eltData.abortable = false;
                if (eltData.queuedRequests != null &&
                    eltData.queuedRequests.length > 0) {
                    var queuedRequest = eltData.queuedRequests.shift();
                    queuedRequest();
                }
            }
            var promptQuestion = getClosestAttributeValue(elt, "hx-prompt");
            if (promptQuestion) {
                var promptResponse = prompt(promptQuestion);
                // prompt returns null if cancelled and empty string if accepted with no entry
                if (promptResponse === null ||
                    !triggerEvent(elt, 'htmx:prompt', {prompt: promptResponse, target:target})) {
                    maybeCall(resolve);
                    endRequestLock();
                    return promise;
                }
            }

            var confirmQuestion = getClosestAttributeValue(elt, "hx-confirm");
            if (confirmQuestion) {
                if(!confirm(confirmQuestion)) {
                    maybeCall(resolve);
                    endRequestLock()
                    return promise;
                }
            }


            var headers = getHeaders(elt, target, promptResponse);
            if (etc.headers) {
                headers = mergeObjects(headers, etc.headers);
            }
            var results = getInputValues(elt, verb);
            var errors = results.errors;
            var rawParameters = results.values;
            if (etc.values) {
                rawParameters = mergeObjects(rawParameters, etc.values);
            }
            var expressionVars = getExpressionVars(elt);
            var allParameters = mergeObjects(rawParameters, expressionVars);
            var filteredParameters = filterValues(allParameters, elt);

            if (verb !== 'get' && !usesFormData(elt)) {
                headers['Content-Type'] = 'application/x-www-form-urlencoded';
            }

            if (htmx.config.getCacheBusterParam && verb === 'get') {
                filteredParameters['org.htmx.cache-buster'] = getRawAttribute(target, "id") || "true";
            }

            // behavior of anchors w/ empty href is to use the current URL
            if (path == null || path === "") {
                path = getDocument().location.href;
            }


            var requestAttrValues = getValuesForElement(elt, 'hx-request');

            var eltIsBoosted = getInternalData(elt).boosted;
            var requestConfig = {
                boosted: eltIsBoosted,
                parameters: filteredParameters,
                unfilteredParameters: allParameters,
                headers:headers,
                target:target,
                verb:verb,
                errors:errors,
                withCredentials: etc.credentials || requestAttrValues.credentials || htmx.config.withCredentials,
                timeout:  etc.timeout || requestAttrValues.timeout || htmx.config.timeout,
                path:path,
                triggeringEvent:event
            };

            if(!triggerEvent(elt, 'htmx:configRequest', requestConfig)){
                maybeCall(resolve);
                endRequestLock();
                return promise;
            }

            // copy out in case the object was overwritten
            path = requestConfig.path;
            verb = requestConfig.verb;
            headers = requestConfig.headers;
            filteredParameters = requestConfig.parameters;
            errors = requestConfig.errors;

            if(errors && errors.length > 0){
                triggerEvent(elt, 'htmx:validation:halted', requestConfig)
                maybeCall(resolve);
                endRequestLock();
                return promise;
            }

            var splitPath = path.split("#");
            var pathNoAnchor = splitPath[0];
            var anchor = splitPath[1];
            var finalPathForGet = null;
            if (verb === 'get') {
                finalPathForGet = pathNoAnchor;
                var values = Object.keys(filteredParameters).length !== 0;
                if (values) {
                    if (finalPathForGet.indexOf("?") < 0) {
                        finalPathForGet += "?";
                    } else {
                        finalPathForGet += "&";
                    }
                    finalPathForGet += urlEncode(filteredParameters);
                    if (anchor) {
                        finalPathForGet += "#" + anchor;
                    }
                }
                xhr.open('GET', finalPathForGet, true);
            } else {
                xhr.open(verb.toUpperCase(), path, true);
            }

            xhr.overrideMimeType("text/html");
            xhr.withCredentials = requestConfig.withCredentials;
            xhr.timeout = requestConfig.timeout;

            // request headers
            if (requestAttrValues.noHeaders) {
                // ignore all headers
            } else {
                for (var header in headers) {
                    if (headers.hasOwnProperty(header)) {
                        var headerValue = headers[header];
                        safelySetHeaderValue(xhr, header, headerValue);
                    }
                }
            }

            var responseInfo = {
                xhr: xhr, target: target, requestConfig: requestConfig, etc: etc, boosted: eltIsBoosted,
                pathInfo: {
                    requestPath: path,
                    finalRequestPath: finalPathForGet || path,
                    anchor: anchor
                }
            };

            xhr.onload = function () {
                try {
                    var hierarchy = hierarchyForElt(elt);
                    responseInfo.pathInfo.responsePath = getPathFromResponse(xhr);
                    responseHandler(elt, responseInfo);
                    removeRequestIndicatorClasses(indicators);
                    triggerEvent(elt, 'htmx:afterRequest', responseInfo);
                    triggerEvent(elt, 'htmx:afterOnLoad', responseInfo);
                    // if the body no longer contains the element, trigger the event on the closest parent
                    // remaining in the DOM
                    if (!bodyContains(elt)) {
                        var secondaryTriggerElt = null;
                        while (hierarchy.length > 0 && secondaryTriggerElt == null) {
                            var parentEltInHierarchy = hierarchy.shift();
                            if (bodyContains(parentEltInHierarchy)) {
                                secondaryTriggerElt = parentEltInHierarchy;
                            }
                        }
                        if (secondaryTriggerElt) {
                            triggerEvent(secondaryTriggerElt, 'htmx:afterRequest', responseInfo);
                            triggerEvent(secondaryTriggerElt, 'htmx:afterOnLoad', responseInfo);
                        }
                    }
                    maybeCall(resolve);
                    endRequestLock();
                } catch (e) {
                    triggerErrorEvent(elt, 'htmx:onLoadError', mergeObjects({error:e}, responseInfo));
                    throw e;
                }
            }
            xhr.onerror = function () {
                removeRequestIndicatorClasses(indicators);
                triggerErrorEvent(elt, 'htmx:afterRequest', responseInfo);
                triggerErrorEvent(elt, 'htmx:sendError', responseInfo);
                maybeCall(reject);
                endRequestLock();
            }
            xhr.onabort = function() {
                removeRequestIndicatorClasses(indicators);
                triggerErrorEvent(elt, 'htmx:afterRequest', responseInfo);
                triggerErrorEvent(elt, 'htmx:sendAbort', responseInfo);
                maybeCall(reject);
                endRequestLock();
            }
            xhr.ontimeout = function() {
                removeRequestIndicatorClasses(indicators);
                triggerErrorEvent(elt, 'htmx:afterRequest', responseInfo);
                triggerErrorEvent(elt, 'htmx:timeout', responseInfo);
                maybeCall(reject);
                endRequestLock();
            }
            if(!triggerEvent(elt, 'htmx:beforeRequest', responseInfo)){
                maybeCall(resolve);
                endRequestLock()
                return promise
            }
            var indicators = addRequestIndicatorClasses(elt);

            forEach(['loadstart', 'loadend', 'progress', 'abort'], function(eventName) {
                forEach([xhr, xhr.upload], function (target) {
                    target.addEventListener(eventName, function(event){
                        triggerEvent(elt, "htmx:xhr:" + eventName, {
                            lengthComputable:event.lengthComputable,
                            loaded:event.loaded,
                            total:event.total
                        });
                    })
                });
            });
            triggerEvent(elt, 'htmx:beforeSend', responseInfo);
            xhr.send(verb === 'get' ? null : encodeParamsForBody(xhr, elt, filteredParameters));
            return promise;
        }

        function determineHistoryUpdates(elt, responseInfo) {

            var xhr = responseInfo.xhr;

            //===========================================
            // First consult response headers
            //===========================================
            var pathFromHeaders = null;
            var typeFromHeaders = null;
            if (hasHeader(xhr,/HX-Push:/i)) {
                pathFromHeaders = xhr.getResponseHeader("HX-Push");
                typeFromHeaders = "push";
            } else if (hasHeader(xhr,/HX-Push-Url:/i)) {
                pathFromHeaders = xhr.getResponseHeader("HX-Push-Url");
                typeFromHeaders = "push";
            } else if (hasHeader(xhr,/HX-Replace-Url:/i)) {
                pathFromHeaders = xhr.getResponseHeader("HX-Replace-Url");
                typeFromHeaders = "replace";
            }

            // if there was a response header, that has priority
            if (pathFromHeaders) {
                if (pathFromHeaders === "false") {
                    return {}
                } else {
                    return {
                        type: typeFromHeaders,
                        path : pathFromHeaders
                    }
                }
            }

            //===========================================
            // Next resolve via DOM values
            //===========================================
            var requestPath =  responseInfo.pathInfo.finalRequestPath;
            var responsePath =  responseInfo.pathInfo.responsePath;

            var pushUrl = getClosestAttributeValue(elt, "hx-push-url");
            var replaceUrl = getClosestAttributeValue(elt, "hx-replace-url");
            var elementIsBoosted = getInternalData(elt).boosted;

            var saveType = null;
            var path = null;

            if (pushUrl) {
                saveType = "push";
                path = pushUrl;
            } else if (replaceUrl) {
                saveType = "replace";
                path = replaceUrl;
            } else if (elementIsBoosted) {
                saveType = "push";
                path = responsePath || requestPath; // if there is no response path, go with the original request path
            }

            if (path) {
                // false indicates no push, return empty object
                if (path === "false") {
                    return {};
                }

                // true indicates we want to follow wherever the server ended up sending us
                if (path === "true") {
                    path = responsePath || requestPath; // if there is no response path, go with the original request path
                }

                // restore any anchor associated with the request
                if (responseInfo.pathInfo.anchor &&
                    path.indexOf("#") === -1) {
                    path = path + "#" + responseInfo.pathInfo.anchor;
                }

                return {
                    type:saveType,
                    path: path
                }
            } else {
                return {};
            }
        }

        function handleAjaxResponse(elt, responseInfo) {
            var xhr = responseInfo.xhr;
            var target = responseInfo.target;
            var etc = responseInfo.etc;

            if (!triggerEvent(elt, 'htmx:beforeOnLoad', responseInfo)) return;

            if (hasHeader(xhr, /HX-Trigger:/i)) {
                handleTrigger(xhr, "HX-Trigger", elt);
            }

            if (hasHeader(xhr, /HX-Location:/i)) {
                saveCurrentPageToHistory();
                var redirectPath = xhr.getResponseHeader("HX-Location");
                var swapSpec;
                if (redirectPath.indexOf("{") === 0) {
                    swapSpec = parseJSON(redirectPath);
                    // what's the best way to throw an error if the user didn't include this
                    redirectPath = swapSpec['path'];
                    delete swapSpec['path'];
                }
                ajaxHelper('GET', redirectPath, swapSpec).then(function(){
                    pushUrlIntoHistory(redirectPath);
                });
                return;
            }

            if (hasHeader(xhr, /HX-Redirect:/i)) {
                location.href = xhr.getResponseHeader("HX-Redirect");
                return;
            }

            if (hasHeader(xhr,/HX-Refresh:/i)) {
                if ("true" === xhr.getResponseHeader("HX-Refresh")) {
                    location.reload();
                    return;
                }
            }

            if (hasHeader(xhr,/HX-Retarget:/i)) {
                responseInfo.target = getDocument().querySelector(xhr.getResponseHeader("HX-Retarget"));
            }

            var historyUpdate = determineHistoryUpdates(elt, responseInfo);

            // by default htmx only swaps on 200 return codes and does not swap
            // on 204 'No Content'
            // this can be ovverriden by responding to the htmx:beforeSwap event and
            // overriding the detail.shouldSwap property
            var shouldSwap = xhr.status >= 200 && xhr.status < 400 && xhr.status !== 204;
            var serverResponse = xhr.response;
            var isError = xhr.status >= 400;
            var beforeSwapDetails = mergeObjects({shouldSwap: shouldSwap, serverResponse:serverResponse, isError:isError}, responseInfo);
            if (!triggerEvent(target, 'htmx:beforeSwap', beforeSwapDetails)) return;

            target = beforeSwapDetails.target; // allow re-targeting
            serverResponse = beforeSwapDetails.serverResponse; // allow updating content
            isError = beforeSwapDetails.isError; // allow updating error

            responseInfo.target = target; // Make updated target available to response events
            responseInfo.failed = isError; // Make failed property available to response events
            responseInfo.successful = !isError; // Make successful property available to response events

            if (beforeSwapDetails.shouldSwap) {
                if (xhr.status === 286) {
                    cancelPolling(elt);
                }

                withExtensions(elt, function (extension) {
                    serverResponse = extension.transformResponse(serverResponse, xhr, elt);
                });

                // Save current page if there will be a history update
                if (historyUpdate.type) {
                    saveCurrentPageToHistory();
                }

                var swapOverride = etc.swapOverride;
                if (hasHeader(xhr,/HX-Reswap:/i)) {
                    swapOverride = xhr.getResponseHeader("HX-Reswap");
                }
                var swapSpec = getSwapSpecification(elt, swapOverride);

                target.classList.add(htmx.config.swappingClass);
                var doSwap = function () {
                    try {

                        var activeElt = document.activeElement;
                        var selectionInfo = {};
                        try {
                            selectionInfo = {
                                elt: activeElt,
                                // @ts-ignore
                                start: activeElt ? activeElt.selectionStart : null,
                                // @ts-ignore
                                end: activeElt ? activeElt.selectionEnd : null
                            };
                        } catch (e) {
                            // safari issue - see https://github.com/microsoft/playwright/issues/5894
                        }

                        var settleInfo = makeSettleInfo(target);
                        selectAndSwap(swapSpec.swapStyle, target, elt, serverResponse, settleInfo);

                        if (selectionInfo.elt &&
                            !bodyContains(selectionInfo.elt) &&
                            selectionInfo.elt.id) {
                            var newActiveElt = document.getElementById(selectionInfo.elt.id);
                            var focusOptions = { preventScroll: swapSpec.focusScroll !== undefined ? !swapSpec.focusScroll : !htmx.config.defaultFocusScroll };
                            if (newActiveElt) {
                                // @ts-ignore
                                if (selectionInfo.start && newActiveElt.setSelectionRange) {
                                    // @ts-ignore
                                    try {
                                        newActiveElt.setSelectionRange(selectionInfo.start, selectionInfo.end);
                                    } catch (e) {
                                        // the setSelectionRange method is present on fields that don't support it, so just let this fail
                                    }
                                }
                                newActiveElt.focus(focusOptions);
                            }
                        }

                        target.classList.remove(htmx.config.swappingClass);
                        forEach(settleInfo.elts, function (elt) {
                            if (elt.classList) {
                                elt.classList.add(htmx.config.settlingClass);
                            }
                            triggerEvent(elt, 'htmx:afterSwap', responseInfo);
                        });

                        if (hasHeader(xhr, /HX-Trigger-After-Swap:/i)) {
                            var finalElt = elt;
                            if (!bodyContains(elt)) {
                                finalElt = getDocument().body;
                            }
                            handleTrigger(xhr, "HX-Trigger-After-Swap", finalElt);
                        }

                        var doSettle = function () {
                            forEach(settleInfo.tasks, function (task) {
                                task.call();
                            });
                            forEach(settleInfo.elts, function (elt) {
                                if (elt.classList) {
                                    elt.classList.remove(htmx.config.settlingClass);
                                }
                                triggerEvent(elt, 'htmx:afterSettle', responseInfo);
                            });

                            // if we need to save history, do so
                            if (historyUpdate.type) {
                                if (historyUpdate.type === "push") {
                                    pushUrlIntoHistory(historyUpdate.path);
                                    triggerEvent(getDocument().body, 'htmx:pushedIntoHistory', {path: historyUpdate.path});
                                } else {
                                    replaceUrlInHistory(historyUpdate.path);
                                    triggerEvent(getDocument().body, 'htmx:replacedInHistory', {path: historyUpdate.path});
                                }
                            }
                            if (responseInfo.pathInfo.anchor) {
                                var anchorTarget = find("#" + responseInfo.pathInfo.anchor);
                                if(anchorTarget) {
                                    anchorTarget.scrollIntoView({block:'start', behavior: "auto"});
                                }
                            }

                            if(settleInfo.title) {
                                var titleElt = find("title");
                                if(titleElt) {
                                    titleElt.innerHTML = settleInfo.title;
                                } else {
                                    window.document.title = settleInfo.title;
                                }
                            }

                            updateScrollState(settleInfo.elts, swapSpec);

                            if (hasHeader(xhr, /HX-Trigger-After-Settle:/i)) {
                                var finalElt = elt;
                                if (!bodyContains(elt)) {
                                    finalElt = getDocument().body;
                                }
                                handleTrigger(xhr, "HX-Trigger-After-Settle", finalElt);
                            }
                        }

                        if (swapSpec.settleDelay > 0) {
                            setTimeout(doSettle, swapSpec.settleDelay)
                        } else {
                            doSettle();
                        }
                    } catch (e) {
                        triggerErrorEvent(elt, 'htmx:swapError', responseInfo);
                        throw e;
                    }
                };

                if (swapSpec.swapDelay > 0) {
                    setTimeout(doSwap, swapSpec.swapDelay)
                } else {
                    doSwap();
                }
            }
            if (isError) {
                triggerErrorEvent(elt, 'htmx:responseError', mergeObjects({error: "Response Status Error Code " + xhr.status + " from " + responseInfo.pathInfo.requestPath}, responseInfo));
            }
        }

        //====================================================================
        // Extensions API
        //====================================================================

        /** @type {Object<string, import("./htmx").HtmxExtension>} */
        var extensions = {};

        /**
         * extensionBase defines the default functions for all extensions.
         * @returns {import("./htmx").HtmxExtension}
         */
        function extensionBase() {
            return {
                init: function(api) {return null;},
                onEvent : function(name, evt) {return true;},
                transformResponse : function(text, xhr, elt) {return text;},
                isInlineSwap : function(swapStyle) {return false;},
                handleSwap : function(swapStyle, target, fragment, settleInfo) {return false;},
                encodeParameters : function(xhr, parameters, elt) {return null;}
            }
        }

        /**
         * defineExtension initializes the extension and adds it to the htmx registry
         *
         * @param {string} name
         * @param {import("./htmx").HtmxExtension} extension
         */
        function defineExtension(name, extension) {
            if(extension.init) {
                extension.init(internalAPI)
            }
            extensions[name] = mergeObjects(extensionBase(), extension);
        }

        /**
         * removeExtension removes an extension from the htmx registry
         *
         * @param {string} name
         */
        function removeExtension(name) {
            delete extensions[name];
        }

        /**
         * getExtensions searches up the DOM tree to return all extensions that can be applied to a given element
         *
         * @param {HTMLElement} elt
         * @param {import("./htmx").HtmxExtension[]=} extensionsToReturn
         * @param {import("./htmx").HtmxExtension[]=} extensionsToIgnore
         */
         function getExtensions(elt, extensionsToReturn, extensionsToIgnore) {

            if (elt == undefined) {
                return extensionsToReturn;
            }
            if (extensionsToReturn == undefined) {
                extensionsToReturn = [];
            }
            if (extensionsToIgnore == undefined) {
                extensionsToIgnore = [];
            }
            var extensionsForElement = getAttributeValue(elt, "hx-ext");
            if (extensionsForElement) {
                forEach(extensionsForElement.split(","), function(extensionName){
                    extensionName = extensionName.replace(/ /g, '');
                    if (extensionName.slice(0, 7) == "ignore:") {
                        extensionsToIgnore.push(extensionName.slice(7));
                        return;
                    }
                    if (extensionsToIgnore.indexOf(extensionName) < 0) {
                        var extension = extensions[extensionName];
                        if (extension && extensionsToReturn.indexOf(extension) < 0) {
                            extensionsToReturn.push(extension);
                        }
                    }
                });
            }
            return getExtensions(parentElt(elt), extensionsToReturn, extensionsToIgnore);
        }

        //====================================================================
        // Initialization
        //====================================================================

        function ready(fn) {
            if (getDocument().readyState !== 'loading') {
                fn();
            } else {
                getDocument().addEventListener('DOMContentLoaded', fn);
            }
        }

        function insertIndicatorStyles() {
            if (htmx.config.includeIndicatorStyles !== false) {
                getDocument().head.insertAdjacentHTML("beforeend",
                    "<style>\
                      ." + htmx.config.indicatorClass + "{opacity:0;transition: opacity 200ms ease-in;}\
                      ." + htmx.config.requestClass + " ." + htmx.config.indicatorClass + "{opacity:1}\
                      ." + htmx.config.requestClass + "." + htmx.config.indicatorClass + "{opacity:1}\
                    </style>");
            }
        }

        function getMetaConfig() {
            var element = getDocument().querySelector('meta[name="htmx-config"]');
            if (element) {
                // @ts-ignore
                return parseJSON(element.content);
            } else {
                return null;
            }
        }

        function mergeMetaConfig() {
            var metaConfig = getMetaConfig();
            if (metaConfig) {
                htmx.config = mergeObjects(htmx.config , metaConfig)
            }
        }

        // initialize the document
        ready(function () {
            mergeMetaConfig();
            insertIndicatorStyles();
            var body = getDocument().body;
            processNode(body);
            var restoredElts = getDocument().querySelectorAll(
                "[hx-trigger='restored'],[data-hx-trigger='restored']"
            );
            body.addEventListener("htmx:abort", function (evt) {
                var target = evt.target;
                var internalData = getInternalData(target);
                if (internalData && internalData.xhr) {
                    internalData.xhr.abort();
                }
            });
            window.onpopstate = function (event) {
                if (event.state && event.state.htmx) {
                    restoreHistory();
                    forEach(restoredElts, function(elt){
                        triggerEvent(elt, 'htmx:restored', {
                            'document': getDocument(),
                            'triggerEvent': triggerEvent
                        });
                    });
                }
            };
            setTimeout(function () {
                triggerEvent(body, 'htmx:load', {}); // give ready handlers a chance to load up before firing this event
            }, 0);
        })

        return htmx;
    }
)()
}));

htmx.defineExtension('debug', {
    onEvent: function (name, evt) {
        if (console.debug) {
            console.debug(name, evt);
        } else if (console) {
            console.log("DEBUG:", name, evt);
        } else {
            throw "NO CONSOLE SUPPORTED"
        }
    }
});

/**
 * @popperjs/core v2.11.7 - MIT License
 */

!function (e, t) { "object" == typeof exports && "undefined" != typeof module ? t(exports) : "function" == typeof define && define.amd ? define(["exports"], t) : t((e = "undefined" != typeof globalThis ? globalThis : e || self).Popper = {}); }(this, (function (e) { "use strict"; function t(e) { if (null == e) return window; if ("[object Window]" !== e.toString()) { var t = e.ownerDocument; return t && t.defaultView || window; } return e; } function n(e) { return e instanceof t(e).Element || e instanceof Element; } function r(e) { return e instanceof t(e).HTMLElement || e instanceof HTMLElement; } function o(e) { return "undefined" != typeof ShadowRoot && (e instanceof t(e).ShadowRoot || e instanceof ShadowRoot); } var i = Math.max, a = Math.min, s = Math.round; function f() { var e = navigator.userAgentData; return null != e && e.brands && Array.isArray(e.brands) ? e.brands.map((function (e) { return e.brand + "/" + e.version; })).join(" ") : navigator.userAgent; } function c() { return !/^((?!chrome|android).)*safari/i.test(f()); } function p(e, o, i) { void 0 === o && (o = !1), void 0 === i && (i = !1); var a = e.getBoundingClientRect(), f = 1, p = 1; o && r(e) && (f = e.offsetWidth > 0 && s(a.width) / e.offsetWidth || 1, p = e.offsetHeight > 0 && s(a.height) / e.offsetHeight || 1); var u = (n(e) ? t(e) : window).visualViewport, l = !c() && i, d = (a.left + (l && u ? u.offsetLeft : 0)) / f, h = (a.top + (l && u ? u.offsetTop : 0)) / p, m = a.width / f, v = a.height / p; return { width: m, height: v, top: h, right: d + m, bottom: h + v, left: d, x: d, y: h }; } function u(e) { var n = t(e); return { scrollLeft: n.pageXOffset, scrollTop: n.pageYOffset }; } function l(e) { return e ? (e.nodeName || "").toLowerCase() : null; } function d(e) { return ((n(e) ? e.ownerDocument : e.document) || window.document).documentElement; } function h(e) { return p(d(e)).left + u(e).scrollLeft; } function m(e) { return t(e).getComputedStyle(e); } function v(e) { var t = m(e), n = t.overflow, r = t.overflowX, o = t.overflowY; return /auto|scroll|overlay|hidden/.test(n + o + r); } function y(e, n, o) { void 0 === o && (o = !1); var i, a, f = r(n), c = r(n) && function (e) { var t = e.getBoundingClientRect(), n = s(t.width) / e.offsetWidth || 1, r = s(t.height) / e.offsetHeight || 1; return 1 !== n || 1 !== r; }(n), m = d(n), y = p(e, c, o), g = { scrollLeft: 0, scrollTop: 0 }, b = { x: 0, y: 0 }; return (f || !f && !o) && (("body" !== l(n) || v(m)) && (g = (i = n) !== t(i) && r(i) ? { scrollLeft: (a = i).scrollLeft, scrollTop: a.scrollTop } : u(i)), r(n) ? ((b = p(n, !0)).x += n.clientLeft, b.y += n.clientTop) : m && (b.x = h(m))), { x: y.left + g.scrollLeft - b.x, y: y.top + g.scrollTop - b.y, width: y.width, height: y.height }; } function g(e) { var t = p(e), n = e.offsetWidth, r = e.offsetHeight; return Math.abs(t.width - n) <= 1 && (n = t.width), Math.abs(t.height - r) <= 1 && (r = t.height), { x: e.offsetLeft, y: e.offsetTop, width: n, height: r }; } function b(e) { return "html" === l(e) ? e : e.assignedSlot || e.parentNode || (o(e) ? e.host : null) || d(e); } function x(e) { return ["html", "body", "#document"].indexOf(l(e)) >= 0 ? e.ownerDocument.body : r(e) && v(e) ? e : x(b(e)); } function w(e, n) { var r; void 0 === n && (n = []); var o = x(e), i = o === (null == (r = e.ownerDocument) ? void 0 : r.body), a = t(o), s = i ? [a].concat(a.visualViewport || [], v(o) ? o : []) : o, f = n.concat(s); return i ? f : f.concat(w(b(s))); } function O(e) { return ["table", "td", "th"].indexOf(l(e)) >= 0; } function j(e) { return r(e) && "fixed" !== m(e).position ? e.offsetParent : null; } function E(e) { for (var n = t(e), i = j(e); i && O(i) && "static" === m(i).position;)i = j(i); return i && ("html" === l(i) || "body" === l(i) && "static" === m(i).position) ? n : i || function (e) { var t = /firefox/i.test(f()); if (/Trident/i.test(f()) && r(e) && "fixed" === m(e).position) return null; var n = b(e); for (o(n) && (n = n.host); r(n) && ["html", "body"].indexOf(l(n)) < 0;) { var i = m(n); if ("none" !== i.transform || "none" !== i.perspective || "paint" === i.contain || -1 !== ["transform", "perspective"].indexOf(i.willChange) || t && "filter" === i.willChange || t && i.filter && "none" !== i.filter) return n; n = n.parentNode; } return null; }(e) || n; } var D = "top", A = "bottom", L = "right", P = "left", M = "auto", k = [D, A, L, P], W = "start", B = "end", H = "viewport", T = "popper", R = k.reduce((function (e, t) { return e.concat([t + "-" + W, t + "-" + B]); }), []), S = [].concat(k, [M]).reduce((function (e, t) { return e.concat([t, t + "-" + W, t + "-" + B]); }), []), V = ["beforeRead", "read", "afterRead", "beforeMain", "main", "afterMain", "beforeWrite", "write", "afterWrite"]; function q(e) { var t = new Map, n = new Set, r = []; function o(e) { n.add(e.name), [].concat(e.requires || [], e.requiresIfExists || []).forEach((function (e) { if (!n.has(e)) { var r = t.get(e); r && o(r); } })), r.push(e); } return e.forEach((function (e) { t.set(e.name, e); })), e.forEach((function (e) { n.has(e.name) || o(e); })), r; } function C(e) { return e.split("-")[0]; } function N(e, t) { var n = t.getRootNode && t.getRootNode(); if (e.contains(t)) return !0; if (n && o(n)) { var r = t; do { if (r && e.isSameNode(r)) return !0; r = r.parentNode || r.host; } while (r); } return !1; } function I(e) { return Object.assign({}, e, { left: e.x, top: e.y, right: e.x + e.width, bottom: e.y + e.height }); } function _(e, r, o) { return r === H ? I(function (e, n) { var r = t(e), o = d(e), i = r.visualViewport, a = o.clientWidth, s = o.clientHeight, f = 0, p = 0; if (i) { a = i.width, s = i.height; var u = c(); (u || !u && "fixed" === n) && (f = i.offsetLeft, p = i.offsetTop); } return { width: a, height: s, x: f + h(e), y: p }; }(e, o)) : n(r) ? function (e, t) { var n = p(e, !1, "fixed" === t); return n.top = n.top + e.clientTop, n.left = n.left + e.clientLeft, n.bottom = n.top + e.clientHeight, n.right = n.left + e.clientWidth, n.width = e.clientWidth, n.height = e.clientHeight, n.x = n.left, n.y = n.top, n; }(r, o) : I(function (e) { var t, n = d(e), r = u(e), o = null == (t = e.ownerDocument) ? void 0 : t.body, a = i(n.scrollWidth, n.clientWidth, o ? o.scrollWidth : 0, o ? o.clientWidth : 0), s = i(n.scrollHeight, n.clientHeight, o ? o.scrollHeight : 0, o ? o.clientHeight : 0), f = -r.scrollLeft + h(e), c = -r.scrollTop; return "rtl" === m(o || n).direction && (f += i(n.clientWidth, o ? o.clientWidth : 0) - a), { width: a, height: s, x: f, y: c }; }(d(e))); } function F(e, t, o, s) { var f = "clippingParents" === t ? function (e) { var t = w(b(e)), o = ["absolute", "fixed"].indexOf(m(e).position) >= 0 && r(e) ? E(e) : e; return n(o) ? t.filter((function (e) { return n(e) && N(e, o) && "body" !== l(e); })) : []; }(e) : [].concat(t), c = [].concat(f, [o]), p = c[0], u = c.reduce((function (t, n) { var r = _(e, n, s); return t.top = i(r.top, t.top), t.right = a(r.right, t.right), t.bottom = a(r.bottom, t.bottom), t.left = i(r.left, t.left), t; }), _(e, p, s)); return u.width = u.right - u.left, u.height = u.bottom - u.top, u.x = u.left, u.y = u.top, u; } function U(e) { return e.split("-")[1]; } function z(e) { return ["top", "bottom"].indexOf(e) >= 0 ? "x" : "y"; } function X(e) { var t, n = e.reference, r = e.element, o = e.placement, i = o ? C(o) : null, a = o ? U(o) : null, s = n.x + n.width / 2 - r.width / 2, f = n.y + n.height / 2 - r.height / 2; switch (i) { case D: t = { x: s, y: n.y - r.height }; break; case A: t = { x: s, y: n.y + n.height }; break; case L: t = { x: n.x + n.width, y: f }; break; case P: t = { x: n.x - r.width, y: f }; break; default: t = { x: n.x, y: n.y }; }var c = i ? z(i) : null; if (null != c) { var p = "y" === c ? "height" : "width"; switch (a) { case W: t[c] = t[c] - (n[p] / 2 - r[p] / 2); break; case B: t[c] = t[c] + (n[p] / 2 - r[p] / 2); } } return t; } function Y(e) { return Object.assign({}, { top: 0, right: 0, bottom: 0, left: 0 }, e); } function G(e, t) { return t.reduce((function (t, n) { return t[n] = e, t; }), {}); } function J(e, t) { void 0 === t && (t = {}); var r = t, o = r.placement, i = void 0 === o ? e.placement : o, a = r.strategy, s = void 0 === a ? e.strategy : a, f = r.boundary, c = void 0 === f ? "clippingParents" : f, u = r.rootBoundary, l = void 0 === u ? H : u, h = r.elementContext, m = void 0 === h ? T : h, v = r.altBoundary, y = void 0 !== v && v, g = r.padding, b = void 0 === g ? 0 : g, x = Y("number" != typeof b ? b : G(b, k)), w = m === T ? "reference" : T, O = e.rects.popper, j = e.elements[y ? w : m], E = F(n(j) ? j : j.contextElement || d(e.elements.popper), c, l, s), P = p(e.elements.reference), M = X({ reference: P, element: O, strategy: "absolute", placement: i }), W = I(Object.assign({}, O, M)), B = m === T ? W : P, R = { top: E.top - B.top + x.top, bottom: B.bottom - E.bottom + x.bottom, left: E.left - B.left + x.left, right: B.right - E.right + x.right }, S = e.modifiersData.offset; if (m === T && S) { var V = S[i]; Object.keys(R).forEach((function (e) { var t = [L, A].indexOf(e) >= 0 ? 1 : -1, n = [D, A].indexOf(e) >= 0 ? "y" : "x"; R[e] += V[n] * t; })); } return R; } var K = { placement: "bottom", modifiers: [], strategy: "absolute" }; function Q() { for (var e = arguments.length, t = new Array(e), n = 0; n < e; n++)t[n] = arguments[n]; return !t.some((function (e) { return !(e && "function" == typeof e.getBoundingClientRect); })); } function Z(e) { void 0 === e && (e = {}); var t = e, r = t.defaultModifiers, o = void 0 === r ? [] : r, i = t.defaultOptions, a = void 0 === i ? K : i; return function (e, t, r) { void 0 === r && (r = a); var i, s, f = { placement: "bottom", orderedModifiers: [], options: Object.assign({}, K, a), modifiersData: {}, elements: { reference: e, popper: t }, attributes: {}, styles: {} }, c = [], p = !1, u = { state: f, setOptions: function (r) { var i = "function" == typeof r ? r(f.options) : r; l(), f.options = Object.assign({}, a, f.options, i), f.scrollParents = { reference: n(e) ? w(e) : e.contextElement ? w(e.contextElement) : [], popper: w(t) }; var s, p, d = function (e) { var t = q(e); return V.reduce((function (e, n) { return e.concat(t.filter((function (e) { return e.phase === n; }))); }), []); }((s = [].concat(o, f.options.modifiers), p = s.reduce((function (e, t) { var n = e[t.name]; return e[t.name] = n ? Object.assign({}, n, t, { options: Object.assign({}, n.options, t.options), data: Object.assign({}, n.data, t.data) }) : t, e; }), {}), Object.keys(p).map((function (e) { return p[e]; })))); return f.orderedModifiers = d.filter((function (e) { return e.enabled; })), f.orderedModifiers.forEach((function (e) { var t = e.name, n = e.options, r = void 0 === n ? {} : n, o = e.effect; if ("function" == typeof o) { var i = o({ state: f, name: t, instance: u, options: r }), a = function () { }; c.push(i || a); } })), u.update(); }, forceUpdate: function () { if (!p) { var e = f.elements, t = e.reference, n = e.popper; if (Q(t, n)) { f.rects = { reference: y(t, E(n), "fixed" === f.options.strategy), popper: g(n) }, f.reset = !1, f.placement = f.options.placement, f.orderedModifiers.forEach((function (e) { return f.modifiersData[e.name] = Object.assign({}, e.data); })); for (var r = 0; r < f.orderedModifiers.length; r++)if (!0 !== f.reset) { var o = f.orderedModifiers[r], i = o.fn, a = o.options, s = void 0 === a ? {} : a, c = o.name; "function" == typeof i && (f = i({ state: f, options: s, name: c, instance: u }) || f); } else f.reset = !1, r = -1; } } }, update: (i = function () { return new Promise((function (e) { u.forceUpdate(), e(f); })); }, function () { return s || (s = new Promise((function (e) { Promise.resolve().then((function () { s = void 0, e(i()); })); }))), s; }), destroy: function () { l(), p = !0; } }; if (!Q(e, t)) return u; function l() { c.forEach((function (e) { return e(); })), c = []; } return u.setOptions(r).then((function (e) { !p && r.onFirstUpdate && r.onFirstUpdate(e); })), u; }; } var $ = { passive: !0 }; var ee = { name: "eventListeners", enabled: !0, phase: "write", fn: function () { }, effect: function (e) { var n = e.state, r = e.instance, o = e.options, i = o.scroll, a = void 0 === i || i, s = o.resize, f = void 0 === s || s, c = t(n.elements.popper), p = [].concat(n.scrollParents.reference, n.scrollParents.popper); return a && p.forEach((function (e) { e.addEventListener("scroll", r.update, $); })), f && c.addEventListener("resize", r.update, $), function () { a && p.forEach((function (e) { e.removeEventListener("scroll", r.update, $); })), f && c.removeEventListener("resize", r.update, $); }; }, data: {} }; var te = { name: "popperOffsets", enabled: !0, phase: "read", fn: function (e) { var t = e.state, n = e.name; t.modifiersData[n] = X({ reference: t.rects.reference, element: t.rects.popper, strategy: "absolute", placement: t.placement }); }, data: {} }, ne = { top: "auto", right: "auto", bottom: "auto", left: "auto" }; function re(e) { var n, r = e.popper, o = e.popperRect, i = e.placement, a = e.variation, f = e.offsets, c = e.position, p = e.gpuAcceleration, u = e.adaptive, l = e.roundOffsets, h = e.isFixed, v = f.x, y = void 0 === v ? 0 : v, g = f.y, b = void 0 === g ? 0 : g, x = "function" == typeof l ? l({ x: y, y: b }) : { x: y, y: b }; y = x.x, b = x.y; var w = f.hasOwnProperty("x"), O = f.hasOwnProperty("y"), j = P, M = D, k = window; if (u) { var W = E(r), H = "clientHeight", T = "clientWidth"; if (W === t(r) && "static" !== m(W = d(r)).position && "absolute" === c && (H = "scrollHeight", T = "scrollWidth"), W = W, i === D || (i === P || i === L) && a === B) M = A, b -= (h && W === k && k.visualViewport ? k.visualViewport.height : W[H]) - o.height, b *= p ? 1 : -1; if (i === P || (i === D || i === A) && a === B) j = L, y -= (h && W === k && k.visualViewport ? k.visualViewport.width : W[T]) - o.width, y *= p ? 1 : -1; } var R, S = Object.assign({ position: c }, u && ne), V = !0 === l ? function (e, t) { var n = e.x, r = e.y, o = t.devicePixelRatio || 1; return { x: s(n * o) / o || 0, y: s(r * o) / o || 0 }; }({ x: y, y: b }, t(r)) : { x: y, y: b }; return y = V.x, b = V.y, p ? Object.assign({}, S, ((R = {})[M] = O ? "0" : "", R[j] = w ? "0" : "", R.transform = (k.devicePixelRatio || 1) <= 1 ? "translate(" + y + "px, " + b + "px)" : "translate3d(" + y + "px, " + b + "px, 0)", R)) : Object.assign({}, S, ((n = {})[M] = O ? b + "px" : "", n[j] = w ? y + "px" : "", n.transform = "", n)); } var oe = { name: "computeStyles", enabled: !0, phase: "beforeWrite", fn: function (e) { var t = e.state, n = e.options, r = n.gpuAcceleration, o = void 0 === r || r, i = n.adaptive, a = void 0 === i || i, s = n.roundOffsets, f = void 0 === s || s, c = { placement: C(t.placement), variation: U(t.placement), popper: t.elements.popper, popperRect: t.rects.popper, gpuAcceleration: o, isFixed: "fixed" === t.options.strategy }; null != t.modifiersData.popperOffsets && (t.styles.popper = Object.assign({}, t.styles.popper, re(Object.assign({}, c, { offsets: t.modifiersData.popperOffsets, position: t.options.strategy, adaptive: a, roundOffsets: f })))), null != t.modifiersData.arrow && (t.styles.arrow = Object.assign({}, t.styles.arrow, re(Object.assign({}, c, { offsets: t.modifiersData.arrow, position: "absolute", adaptive: !1, roundOffsets: f })))), t.attributes.popper = Object.assign({}, t.attributes.popper, { "data-popper-placement": t.placement }); }, data: {} }; var ie = { name: "applyStyles", enabled: !0, phase: "write", fn: function (e) { var t = e.state; Object.keys(t.elements).forEach((function (e) { var n = t.styles[e] || {}, o = t.attributes[e] || {}, i = t.elements[e]; r(i) && l(i) && (Object.assign(i.style, n), Object.keys(o).forEach((function (e) { var t = o[e]; !1 === t ? i.removeAttribute(e) : i.setAttribute(e, !0 === t ? "" : t); }))); })); }, effect: function (e) { var t = e.state, n = { popper: { position: t.options.strategy, left: "0", top: "0", margin: "0" }, arrow: { position: "absolute" }, reference: {} }; return Object.assign(t.elements.popper.style, n.popper), t.styles = n, t.elements.arrow && Object.assign(t.elements.arrow.style, n.arrow), function () { Object.keys(t.elements).forEach((function (e) { var o = t.elements[e], i = t.attributes[e] || {}, a = Object.keys(t.styles.hasOwnProperty(e) ? t.styles[e] : n[e]).reduce((function (e, t) { return e[t] = "", e; }), {}); r(o) && l(o) && (Object.assign(o.style, a), Object.keys(i).forEach((function (e) { o.removeAttribute(e); }))); })); }; }, requires: ["computeStyles"] }; var ae = { name: "offset", enabled: !0, phase: "main", requires: ["popperOffsets"], fn: function (e) { var t = e.state, n = e.options, r = e.name, o = n.offset, i = void 0 === o ? [0, 0] : o, a = S.reduce((function (e, n) { return e[n] = function (e, t, n) { var r = C(e), o = [P, D].indexOf(r) >= 0 ? -1 : 1, i = "function" == typeof n ? n(Object.assign({}, t, { placement: e })) : n, a = i[0], s = i[1]; return a = a || 0, s = (s || 0) * o, [P, L].indexOf(r) >= 0 ? { x: s, y: a } : { x: a, y: s }; }(n, t.rects, i), e; }), {}), s = a[t.placement], f = s.x, c = s.y; null != t.modifiersData.popperOffsets && (t.modifiersData.popperOffsets.x += f, t.modifiersData.popperOffsets.y += c), t.modifiersData[r] = a; } }, se = { left: "right", right: "left", bottom: "top", top: "bottom" }; function fe(e) { return e.replace(/left|right|bottom|top/g, (function (e) { return se[e]; })); } var ce = { start: "end", end: "start" }; function pe(e) { return e.replace(/start|end/g, (function (e) { return ce[e]; })); } function ue(e, t) { void 0 === t && (t = {}); var n = t, r = n.placement, o = n.boundary, i = n.rootBoundary, a = n.padding, s = n.flipVariations, f = n.allowedAutoPlacements, c = void 0 === f ? S : f, p = U(r), u = p ? s ? R : R.filter((function (e) { return U(e) === p; })) : k, l = u.filter((function (e) { return c.indexOf(e) >= 0; })); 0 === l.length && (l = u); var d = l.reduce((function (t, n) { return t[n] = J(e, { placement: n, boundary: o, rootBoundary: i, padding: a })[C(n)], t; }), {}); return Object.keys(d).sort((function (e, t) { return d[e] - d[t]; })); } var le = { name: "flip", enabled: !0, phase: "main", fn: function (e) { var t = e.state, n = e.options, r = e.name; if (!t.modifiersData[r]._skip) { for (var o = n.mainAxis, i = void 0 === o || o, a = n.altAxis, s = void 0 === a || a, f = n.fallbackPlacements, c = n.padding, p = n.boundary, u = n.rootBoundary, l = n.altBoundary, d = n.flipVariations, h = void 0 === d || d, m = n.allowedAutoPlacements, v = t.options.placement, y = C(v), g = f || (y === v || !h ? [fe(v)] : function (e) { if (C(e) === M) return []; var t = fe(e); return [pe(e), t, pe(t)]; }(v)), b = [v].concat(g).reduce((function (e, n) { return e.concat(C(n) === M ? ue(t, { placement: n, boundary: p, rootBoundary: u, padding: c, flipVariations: h, allowedAutoPlacements: m }) : n); }), []), x = t.rects.reference, w = t.rects.popper, O = new Map, j = !0, E = b[0], k = 0; k < b.length; k++) { var B = b[k], H = C(B), T = U(B) === W, R = [D, A].indexOf(H) >= 0, S = R ? "width" : "height", V = J(t, { placement: B, boundary: p, rootBoundary: u, altBoundary: l, padding: c }), q = R ? T ? L : P : T ? A : D; x[S] > w[S] && (q = fe(q)); var N = fe(q), I = []; if (i && I.push(V[H] <= 0), s && I.push(V[q] <= 0, V[N] <= 0), I.every((function (e) { return e; }))) { E = B, j = !1; break; } O.set(B, I); } if (j) for (var _ = function (e) { var t = b.find((function (t) { var n = O.get(t); if (n) return n.slice(0, e).every((function (e) { return e; })); })); if (t) return E = t, "break"; }, F = h ? 3 : 1; F > 0; F--) { if ("break" === _(F)) break; } t.placement !== E && (t.modifiersData[r]._skip = !0, t.placement = E, t.reset = !0); } }, requiresIfExists: ["offset"], data: { _skip: !1 } }; function de(e, t, n) { return i(e, a(t, n)); } var he = { name: "preventOverflow", enabled: !0, phase: "main", fn: function (e) { var t = e.state, n = e.options, r = e.name, o = n.mainAxis, s = void 0 === o || o, f = n.altAxis, c = void 0 !== f && f, p = n.boundary, u = n.rootBoundary, l = n.altBoundary, d = n.padding, h = n.tether, m = void 0 === h || h, v = n.tetherOffset, y = void 0 === v ? 0 : v, b = J(t, { boundary: p, rootBoundary: u, padding: d, altBoundary: l }), x = C(t.placement), w = U(t.placement), O = !w, j = z(x), M = "x" === j ? "y" : "x", k = t.modifiersData.popperOffsets, B = t.rects.reference, H = t.rects.popper, T = "function" == typeof y ? y(Object.assign({}, t.rects, { placement: t.placement })) : y, R = "number" == typeof T ? { mainAxis: T, altAxis: T } : Object.assign({ mainAxis: 0, altAxis: 0 }, T), S = t.modifiersData.offset ? t.modifiersData.offset[t.placement] : null, V = { x: 0, y: 0 }; if (k) { if (s) { var q, N = "y" === j ? D : P, I = "y" === j ? A : L, _ = "y" === j ? "height" : "width", F = k[j], X = F + b[N], Y = F - b[I], G = m ? -H[_] / 2 : 0, K = w === W ? B[_] : H[_], Q = w === W ? -H[_] : -B[_], Z = t.elements.arrow, $ = m && Z ? g(Z) : { width: 0, height: 0 }, ee = t.modifiersData["arrow#persistent"] ? t.modifiersData["arrow#persistent"].padding : { top: 0, right: 0, bottom: 0, left: 0 }, te = ee[N], ne = ee[I], re = de(0, B[_], $[_]), oe = O ? B[_] / 2 - G - re - te - R.mainAxis : K - re - te - R.mainAxis, ie = O ? -B[_] / 2 + G + re + ne + R.mainAxis : Q + re + ne + R.mainAxis, ae = t.elements.arrow && E(t.elements.arrow), se = ae ? "y" === j ? ae.clientTop || 0 : ae.clientLeft || 0 : 0, fe = null != (q = null == S ? void 0 : S[j]) ? q : 0, ce = F + ie - fe, pe = de(m ? a(X, F + oe - fe - se) : X, F, m ? i(Y, ce) : Y); k[j] = pe, V[j] = pe - F; } if (c) { var ue, le = "x" === j ? D : P, he = "x" === j ? A : L, me = k[M], ve = "y" === M ? "height" : "width", ye = me + b[le], ge = me - b[he], be = -1 !== [D, P].indexOf(x), xe = null != (ue = null == S ? void 0 : S[M]) ? ue : 0, we = be ? ye : me - B[ve] - H[ve] - xe + R.altAxis, Oe = be ? me + B[ve] + H[ve] - xe - R.altAxis : ge, je = m && be ? function (e, t, n) { var r = de(e, t, n); return r > n ? n : r; }(we, me, Oe) : de(m ? we : ye, me, m ? Oe : ge); k[M] = je, V[M] = je - me; } t.modifiersData[r] = V; } }, requiresIfExists: ["offset"] }; var me = { name: "arrow", enabled: !0, phase: "main", fn: function (e) { var t, n = e.state, r = e.name, o = e.options, i = n.elements.arrow, a = n.modifiersData.popperOffsets, s = C(n.placement), f = z(s), c = [P, L].indexOf(s) >= 0 ? "height" : "width"; if (i && a) { var p = function (e, t) { return Y("number" != typeof (e = "function" == typeof e ? e(Object.assign({}, t.rects, { placement: t.placement })) : e) ? e : G(e, k)); }(o.padding, n), u = g(i), l = "y" === f ? D : P, d = "y" === f ? A : L, h = n.rects.reference[c] + n.rects.reference[f] - a[f] - n.rects.popper[c], m = a[f] - n.rects.reference[f], v = E(i), y = v ? "y" === f ? v.clientHeight || 0 : v.clientWidth || 0 : 0, b = h / 2 - m / 2, x = p[l], w = y - u[c] - p[d], O = y / 2 - u[c] / 2 + b, j = de(x, O, w), M = f; n.modifiersData[r] = ((t = {})[M] = j, t.centerOffset = j - O, t); } }, effect: function (e) { var t = e.state, n = e.options.element, r = void 0 === n ? "[data-popper-arrow]" : n; null != r && ("string" != typeof r || (r = t.elements.popper.querySelector(r))) && N(t.elements.popper, r) && (t.elements.arrow = r); }, requires: ["popperOffsets"], requiresIfExists: ["preventOverflow"] }; function ve(e, t, n) { return void 0 === n && (n = { x: 0, y: 0 }), { top: e.top - t.height - n.y, right: e.right - t.width + n.x, bottom: e.bottom - t.height + n.y, left: e.left - t.width - n.x }; } function ye(e) { return [D, L, A, P].some((function (t) { return e[t] >= 0; })); } var ge = { name: "hide", enabled: !0, phase: "main", requiresIfExists: ["preventOverflow"], fn: function (e) { var t = e.state, n = e.name, r = t.rects.reference, o = t.rects.popper, i = t.modifiersData.preventOverflow, a = J(t, { elementContext: "reference" }), s = J(t, { altBoundary: !0 }), f = ve(a, r), c = ve(s, o, i), p = ye(f), u = ye(c); t.modifiersData[n] = { referenceClippingOffsets: f, popperEscapeOffsets: c, isReferenceHidden: p, hasPopperEscaped: u }, t.attributes.popper = Object.assign({}, t.attributes.popper, { "data-popper-reference-hidden": p, "data-popper-escaped": u }); } }, be = Z({ defaultModifiers: [ee, te, oe, ie] }), xe = [ee, te, oe, ie, ae, le, he, me, ge], we = Z({ defaultModifiers: xe }); e.applyStyles = ie, e.arrow = me, e.computeStyles = oe, e.createPopper = we, e.createPopperLite = be, e.defaultModifiers = xe, e.detectOverflow = J, e.eventListeners = ee, e.flip = le, e.hide = ge, e.offset = ae, e.popperGenerator = Z, e.popperOffsets = te, e.preventOverflow = he, Object.defineProperty(e, "__esModule", { value: !0 }); }));



!function (t, e) { "object" == typeof exports && "undefined" != typeof module ? module.exports = e(require("@popperjs/core")) : "function" == typeof define && define.amd ? define(["@popperjs/core"], e) : (t = t || self).tippy = e(t.Popper); }(this, (function (t) { "use strict"; var e = "undefined" != typeof window && "undefined" != typeof document, n = !!e && !!window.msCrypto, r = { passive: !0, capture: !0 }, o = function () { return document.body; }; function i(t, e, n) { if (Array.isArray(t)) { var r = t[e]; return null == r ? Array.isArray(n) ? n[e] : n : r; } return t; } function a(t, e) { var n = {}.toString.call(t); return 0 === n.indexOf("[object") && n.indexOf(e + "]") > -1; } function s(t, e) { return "function" == typeof t ? t.apply(void 0, e) : t; } function u(t, e) { return 0 === e ? t : function (r) { clearTimeout(n), n = setTimeout((function () { t(r); }), e); }; var n; } function p(t, e) { var n = Object.assign({}, t); return e.forEach((function (t) { delete n[t]; })), n; } function c(t) { return [].concat(t); } function f(t, e) { -1 === t.indexOf(e) && t.push(e); } function l(t) { return t.split("-")[0]; } function d(t) { return [].slice.call(t); } function v(t) { return Object.keys(t).reduce((function (e, n) { return void 0 !== t[n] && (e[n] = t[n]), e; }), {}); } function m() { return document.createElement("div"); } function g(t) { return ["Element", "Fragment"].some((function (e) { return a(t, e); })); } function h(t) { return a(t, "MouseEvent"); } function b(t) { return !(!t || !t._tippy || t._tippy.reference !== t); } function y(t) { return g(t) ? [t] : function (t) { return a(t, "NodeList"); }(t) ? d(t) : Array.isArray(t) ? t : d(document.querySelectorAll(t)); } function w(t, e) { t.forEach((function (t) { t && (t.style.transitionDuration = e + "ms"); })); } function x(t, e) { t.forEach((function (t) { t && t.setAttribute("data-state", e); })); } function E(t) { var e, n = c(t)[0]; return null != n && null != (e = n.ownerDocument) && e.body ? n.ownerDocument : document; } function O(t, e, n) { var r = e + "EventListener";["transitionend", "webkitTransitionEnd"].forEach((function (e) { t[r](e, n); })); } function C(t, e) { for (var n = e; n;) { var r; if (t.contains(n)) return !0; n = null == n.getRootNode || null == (r = n.getRootNode()) ? void 0 : r.host; } return !1; } var T = { isTouch: !1 }, A = 0; function L() { T.isTouch || (T.isTouch = !0, window.performance && document.addEventListener("mousemove", D)); } function D() { var t = performance.now(); t - A < 20 && (T.isTouch = !1, document.removeEventListener("mousemove", D)), A = t; } function k() { var t = document.activeElement; if (b(t)) { var e = t._tippy; t.blur && !e.state.isVisible && t.blur(); } } var R = Object.assign({ appendTo: o, aria: { content: "auto", expanded: "auto" }, delay: 0, duration: [300, 250], getReferenceClientRect: null, hideOnClick: !0, ignoreAttributes: !1, interactive: !1, interactiveBorder: 2, interactiveDebounce: 0, moveTransition: "", offset: [0, 10], onAfterUpdate: function () { }, onBeforeUpdate: function () { }, onCreate: function () { }, onDestroy: function () { }, onHidden: function () { }, onHide: function () { }, onMount: function () { }, onShow: function () { }, onShown: function () { }, onTrigger: function () { }, onUntrigger: function () { }, onClickOutside: function () { }, placement: "top", plugins: [], popperOptions: {}, render: null, showOnCreate: !1, touch: !0, trigger: "mouseenter focus", triggerTarget: null }, { animateFill: !1, followCursor: !1, inlinePositioning: !1, sticky: !1 }, { allowHTML: !1, animation: "fade", arrow: !0, content: "", inertia: !1, maxWidth: 350, role: "tooltip", theme: "", zIndex: 9999 }), P = Object.keys(R); function j(t) { var e = (t.plugins || []).reduce((function (e, n) { var r, o = n.name, i = n.defaultValue; o && (e[o] = void 0 !== t[o] ? t[o] : null != (r = R[o]) ? r : i); return e; }), {}); return Object.assign({}, t, e); } function M(t, e) { var n = Object.assign({}, e, { content: s(e.content, [t]) }, e.ignoreAttributes ? {} : function (t, e) { return (e ? Object.keys(j(Object.assign({}, R, { plugins: e }))) : P).reduce((function (e, n) { var r = (t.getAttribute("data-tippy-" + n) || "").trim(); if (!r) return e; if ("content" === n) e[n] = r; else try { e[n] = JSON.parse(r); } catch (t) { e[n] = r; } return e; }), {}); }(t, e.plugins)); return n.aria = Object.assign({}, R.aria, n.aria), n.aria = { expanded: "auto" === n.aria.expanded ? e.interactive : n.aria.expanded, content: "auto" === n.aria.content ? e.interactive ? null : "describedby" : n.aria.content }, n; } function V(t, e) { t.innerHTML = e; } function I(t) { var e = m(); return !0 === t ? e.className = "tippy-arrow" : (e.className = "tippy-svg-arrow", g(t) ? e.appendChild(t) : V(e, t)), e; } function S(t, e) { g(e.content) ? (V(t, ""), t.appendChild(e.content)) : "function" != typeof e.content && (e.allowHTML ? V(t, e.content) : t.textContent = e.content); } function B(t) { var e = t.firstElementChild, n = d(e.children); return { box: e, content: n.find((function (t) { return t.classList.contains("tippy-content"); })), arrow: n.find((function (t) { return t.classList.contains("tippy-arrow") || t.classList.contains("tippy-svg-arrow"); })), backdrop: n.find((function (t) { return t.classList.contains("tippy-backdrop"); })) }; } function N(t) { var e = m(), n = m(); n.className = "tippy-box", n.setAttribute("data-state", "hidden"), n.setAttribute("tabindex", "-1"); var r = m(); function o(n, r) { var o = B(e), i = o.box, a = o.content, s = o.arrow; r.theme ? i.setAttribute("data-theme", r.theme) : i.removeAttribute("data-theme"), "string" == typeof r.animation ? i.setAttribute("data-animation", r.animation) : i.removeAttribute("data-animation"), r.inertia ? i.setAttribute("data-inertia", "") : i.removeAttribute("data-inertia"), i.style.maxWidth = "number" == typeof r.maxWidth ? r.maxWidth + "px" : r.maxWidth, r.role ? i.setAttribute("role", r.role) : i.removeAttribute("role"), n.content === r.content && n.allowHTML === r.allowHTML || S(a, t.props), r.arrow ? s ? n.arrow !== r.arrow && (i.removeChild(s), i.appendChild(I(r.arrow))) : i.appendChild(I(r.arrow)) : s && i.removeChild(s); } return r.className = "tippy-content", r.setAttribute("data-state", "hidden"), S(r, t.props), e.appendChild(n), n.appendChild(r), o(t.props, t.props), { popper: e, onUpdate: o }; } N.$$tippy = !0; var H = 1, U = [], _ = []; function z(e, a) { var p, g, b, y, A, L, D, k, P = M(e, Object.assign({}, R, j(v(a)))), V = !1, I = !1, S = !1, N = !1, z = [], F = u(wt, P.interactiveDebounce), W = H++, X = (k = P.plugins).filter((function (t, e) { return k.indexOf(t) === e; })), Y = { id: W, reference: e, popper: m(), popperInstance: null, props: P, state: { isEnabled: !0, isVisible: !1, isDestroyed: !1, isMounted: !1, isShown: !1 }, plugins: X, clearDelayTimeouts: function () { clearTimeout(p), clearTimeout(g), cancelAnimationFrame(b); }, setProps: function (t) { if (Y.state.isDestroyed) return; at("onBeforeUpdate", [Y, t]), bt(); var n = Y.props, r = M(e, Object.assign({}, n, v(t), { ignoreAttributes: !0 })); Y.props = r, ht(), n.interactiveDebounce !== r.interactiveDebounce && (pt(), F = u(wt, r.interactiveDebounce)); n.triggerTarget && !r.triggerTarget ? c(n.triggerTarget).forEach((function (t) { t.removeAttribute("aria-expanded"); })) : r.triggerTarget && e.removeAttribute("aria-expanded"); ut(), it(), J && J(n, r); Y.popperInstance && (Ct(), At().forEach((function (t) { requestAnimationFrame(t._tippy.popperInstance.forceUpdate); }))); at("onAfterUpdate", [Y, t]); }, setContent: function (t) { Y.setProps({ content: t }); }, show: function () { var t = Y.state.isVisible, e = Y.state.isDestroyed, n = !Y.state.isEnabled, r = T.isTouch && !Y.props.touch, a = i(Y.props.duration, 0, R.duration); if (t || e || n || r) return; if (et().hasAttribute("disabled")) return; if (at("onShow", [Y], !1), !1 === Y.props.onShow(Y)) return; Y.state.isVisible = !0, tt() && ($.style.visibility = "visible"); it(), dt(), Y.state.isMounted || ($.style.transition = "none"); if (tt()) { var u = rt(), p = u.box, c = u.content; w([p, c], 0); } L = function () { var t; if (Y.state.isVisible && !N) { if (N = !0, $.offsetHeight, $.style.transition = Y.props.moveTransition, tt() && Y.props.animation) { var e = rt(), n = e.box, r = e.content; w([n, r], a), x([n, r], "visible"); } st(), ut(), f(_, Y), null == (t = Y.popperInstance) || t.forceUpdate(), at("onMount", [Y]), Y.props.animation && tt() && function (t, e) { mt(t, e); }(a, (function () { Y.state.isShown = !0, at("onShown", [Y]); })); } }, function () { var t, e = Y.props.appendTo, n = et(); t = Y.props.interactive && e === o || "parent" === e ? n.parentNode : s(e, [n]); t.contains($) || t.appendChild($); Y.state.isMounted = !0, Ct(); }(); }, hide: function () { var t = !Y.state.isVisible, e = Y.state.isDestroyed, n = !Y.state.isEnabled, r = i(Y.props.duration, 1, R.duration); if (t || e || n) return; if (at("onHide", [Y], !1), !1 === Y.props.onHide(Y)) return; Y.state.isVisible = !1, Y.state.isShown = !1, N = !1, V = !1, tt() && ($.style.visibility = "hidden"); if (pt(), vt(), it(!0), tt()) { var o = rt(), a = o.box, s = o.content; Y.props.animation && (w([a, s], r), x([a, s], "hidden")); } st(), ut(), Y.props.animation ? tt() && function (t, e) { mt(t, (function () { !Y.state.isVisible && $.parentNode && $.parentNode.contains($) && e(); })); }(r, Y.unmount) : Y.unmount(); }, hideWithInteractivity: function (t) { nt().addEventListener("mousemove", F), f(U, F), F(t); }, enable: function () { Y.state.isEnabled = !0; }, disable: function () { Y.hide(), Y.state.isEnabled = !1; }, unmount: function () { Y.state.isVisible && Y.hide(); if (!Y.state.isMounted) return; Tt(), At().forEach((function (t) { t._tippy.unmount(); })), $.parentNode && $.parentNode.removeChild($); _ = _.filter((function (t) { return t !== Y; })), Y.state.isMounted = !1, at("onHidden", [Y]); }, destroy: function () { if (Y.state.isDestroyed) return; Y.clearDelayTimeouts(), Y.unmount(), bt(), delete e._tippy, Y.state.isDestroyed = !0, at("onDestroy", [Y]); } }; if (!P.render) return Y; var q = P.render(Y), $ = q.popper, J = q.onUpdate; $.setAttribute("data-tippy-root", ""), $.id = "tippy-" + Y.id, Y.popper = $, e._tippy = Y, $._tippy = Y; var G = X.map((function (t) { return t.fn(Y); })), K = e.hasAttribute("aria-expanded"); return ht(), ut(), it(), at("onCreate", [Y]), P.showOnCreate && Lt(), $.addEventListener("mouseenter", (function () { Y.props.interactive && Y.state.isVisible && Y.clearDelayTimeouts(); })), $.addEventListener("mouseleave", (function () { Y.props.interactive && Y.props.trigger.indexOf("mouseenter") >= 0 && nt().addEventListener("mousemove", F); })), Y; function Q() { var t = Y.props.touch; return Array.isArray(t) ? t : [t, 0]; } function Z() { return "hold" === Q()[0]; } function tt() { var t; return !(null == (t = Y.props.render) || !t.$$tippy); } function et() { return D || e; } function nt() { var t = et().parentNode; return t ? E(t) : document; } function rt() { return B($); } function ot(t) { return Y.state.isMounted && !Y.state.isVisible || T.isTouch || y && "focus" === y.type ? 0 : i(Y.props.delay, t ? 0 : 1, R.delay); } function it(t) { void 0 === t && (t = !1), $.style.pointerEvents = Y.props.interactive && !t ? "" : "none", $.style.zIndex = "" + Y.props.zIndex; } function at(t, e, n) { var r; (void 0 === n && (n = !0), G.forEach((function (n) { n[t] && n[t].apply(n, e); })), n) && (r = Y.props)[t].apply(r, e); } function st() { var t = Y.props.aria; if (t.content) { var n = "aria-" + t.content, r = $.id; c(Y.props.triggerTarget || e).forEach((function (t) { var e = t.getAttribute(n); if (Y.state.isVisible) t.setAttribute(n, e ? e + " " + r : r); else { var o = e && e.replace(r, "").trim(); o ? t.setAttribute(n, o) : t.removeAttribute(n); } })); } } function ut() { !K && Y.props.aria.expanded && c(Y.props.triggerTarget || e).forEach((function (t) { Y.props.interactive ? t.setAttribute("aria-expanded", Y.state.isVisible && t === et() ? "true" : "false") : t.removeAttribute("aria-expanded"); })); } function pt() { nt().removeEventListener("mousemove", F), U = U.filter((function (t) { return t !== F; })); } function ct(t) { if (!T.isTouch || !S && "mousedown" !== t.type) { var n = t.composedPath && t.composedPath()[0] || t.target; if (!Y.props.interactive || !C($, n)) { if (c(Y.props.triggerTarget || e).some((function (t) { return C(t, n); }))) { if (T.isTouch) return; if (Y.state.isVisible && Y.props.trigger.indexOf("click") >= 0) return; } else at("onClickOutside", [Y, t]); !0 === Y.props.hideOnClick && (Y.clearDelayTimeouts(), Y.hide(), I = !0, setTimeout((function () { I = !1; })), Y.state.isMounted || vt()); } } } function ft() { S = !0; } function lt() { S = !1; } function dt() { var t = nt(); t.addEventListener("mousedown", ct, !0), t.addEventListener("touchend", ct, r), t.addEventListener("touchstart", lt, r), t.addEventListener("touchmove", ft, r); } function vt() { var t = nt(); t.removeEventListener("mousedown", ct, !0), t.removeEventListener("touchend", ct, r), t.removeEventListener("touchstart", lt, r), t.removeEventListener("touchmove", ft, r); } function mt(t, e) { var n = rt().box; function r(t) { t.target === n && (O(n, "remove", r), e()); } if (0 === t) return e(); O(n, "remove", A), O(n, "add", r), A = r; } function gt(t, n, r) { void 0 === r && (r = !1), c(Y.props.triggerTarget || e).forEach((function (e) { e.addEventListener(t, n, r), z.push({ node: e, eventType: t, handler: n, options: r }); })); } function ht() { var t; Z() && (gt("touchstart", yt, { passive: !0 }), gt("touchend", xt, { passive: !0 })), (t = Y.props.trigger, t.split(/\s+/).filter(Boolean)).forEach((function (t) { if ("manual" !== t) switch (gt(t, yt), t) { case "mouseenter": gt("mouseleave", xt); break; case "focus": gt(n ? "focusout" : "blur", Et); break; case "focusin": gt("focusout", Et); } })); } function bt() { z.forEach((function (t) { var e = t.node, n = t.eventType, r = t.handler, o = t.options; e.removeEventListener(n, r, o); })), z = []; } function yt(t) { var e, n = !1; if (Y.state.isEnabled && !Ot(t) && !I) { var r = "focus" === (null == (e = y) ? void 0 : e.type); y = t, D = t.currentTarget, ut(), !Y.state.isVisible && h(t) && U.forEach((function (e) { return e(t); })), "click" === t.type && (Y.props.trigger.indexOf("mouseenter") < 0 || V) && !1 !== Y.props.hideOnClick && Y.state.isVisible ? n = !0 : Lt(t), "click" === t.type && (V = !n), n && !r && Dt(t); } } function wt(t) { var e = t.target, n = et().contains(e) || $.contains(e); "mousemove" === t.type && n || function (t, e) { var n = e.clientX, r = e.clientY; return t.every((function (t) { var e = t.popperRect, o = t.popperState, i = t.props.interactiveBorder, a = l(o.placement), s = o.modifiersData.offset; if (!s) return !0; var u = "bottom" === a ? s.top.y : 0, p = "top" === a ? s.bottom.y : 0, c = "right" === a ? s.left.x : 0, f = "left" === a ? s.right.x : 0, d = e.top - r + u > i, v = r - e.bottom - p > i, m = e.left - n + c > i, g = n - e.right - f > i; return d || v || m || g; })); }(At().concat($).map((function (t) { var e, n = null == (e = t._tippy.popperInstance) ? void 0 : e.state; return n ? { popperRect: t.getBoundingClientRect(), popperState: n, props: P } : null; })).filter(Boolean), t) && (pt(), Dt(t)); } function xt(t) { Ot(t) || Y.props.trigger.indexOf("click") >= 0 && V || (Y.props.interactive ? Y.hideWithInteractivity(t) : Dt(t)); } function Et(t) { Y.props.trigger.indexOf("focusin") < 0 && t.target !== et() || Y.props.interactive && t.relatedTarget && $.contains(t.relatedTarget) || Dt(t); } function Ot(t) { return !!T.isTouch && Z() !== t.type.indexOf("touch") >= 0; } function Ct() { Tt(); var n = Y.props, r = n.popperOptions, o = n.placement, i = n.offset, a = n.getReferenceClientRect, s = n.moveTransition, u = tt() ? B($).arrow : null, p = a ? { getBoundingClientRect: a, contextElement: a.contextElement || et() } : e, c = [{ name: "offset", options: { offset: i } }, { name: "preventOverflow", options: { padding: { top: 2, bottom: 2, left: 5, right: 5 } } }, { name: "flip", options: { padding: 5 } }, { name: "computeStyles", options: { adaptive: !s } }, { name: "$$tippy", enabled: !0, phase: "beforeWrite", requires: ["computeStyles"], fn: function (t) { var e = t.state; if (tt()) { var n = rt().box;["placement", "reference-hidden", "escaped"].forEach((function (t) { "placement" === t ? n.setAttribute("data-placement", e.placement) : e.attributes.popper["data-popper-" + t] ? n.setAttribute("data-" + t, "") : n.removeAttribute("data-" + t); })), e.attributes.popper = {}; } } }]; tt() && u && c.push({ name: "arrow", options: { element: u, padding: 3 } }), c.push.apply(c, (null == r ? void 0 : r.modifiers) || []), Y.popperInstance = t.createPopper(p, $, Object.assign({}, r, { placement: o, onFirstUpdate: L, modifiers: c })); } function Tt() { Y.popperInstance && (Y.popperInstance.destroy(), Y.popperInstance = null); } function At() { return d($.querySelectorAll("[data-tippy-root]")); } function Lt(t) { Y.clearDelayTimeouts(), t && at("onTrigger", [Y, t]), dt(); var e = ot(!0), n = Q(), r = n[0], o = n[1]; T.isTouch && "hold" === r && o && (e = o), e ? p = setTimeout((function () { Y.show(); }), e) : Y.show(); } function Dt(t) { if (Y.clearDelayTimeouts(), at("onUntrigger", [Y, t]), Y.state.isVisible) { if (!(Y.props.trigger.indexOf("mouseenter") >= 0 && Y.props.trigger.indexOf("click") >= 0 && ["mouseleave", "mousemove"].indexOf(t.type) >= 0 && V)) { var e = ot(!1); e ? g = setTimeout((function () { Y.state.isVisible && Y.hide(); }), e) : b = requestAnimationFrame((function () { Y.hide(); })); } } else vt(); } } function F(t, e) { void 0 === e && (e = {}); var n = R.plugins.concat(e.plugins || []); document.addEventListener("touchstart", L, r), window.addEventListener("blur", k); var o = Object.assign({}, e, { plugins: n }), i = y(t).reduce((function (t, e) { var n = e && z(e, o); return n && t.push(n), t; }), []); return g(t) ? i[0] : i; } F.defaultProps = R, F.setDefaultProps = function (t) { Object.keys(t).forEach((function (e) { R[e] = t[e]; })); }, F.currentInput = T; var W = Object.assign({}, t.applyStyles, { effect: function (t) { var e = t.state, n = { popper: { position: e.options.strategy, left: "0", top: "0", margin: "0" }, arrow: { position: "absolute" }, reference: {} }; Object.assign(e.elements.popper.style, n.popper), e.styles = n, e.elements.arrow && Object.assign(e.elements.arrow.style, n.arrow); } }), X = { mouseover: "mouseenter", focusin: "focus", click: "click" }; var Y = { name: "animateFill", defaultValue: !1, fn: function (t) { var e; if (null == (e = t.props.render) || !e.$$tippy) return {}; var n = B(t.popper), r = n.box, o = n.content, i = t.props.animateFill ? function () { var t = m(); return t.className = "tippy-backdrop", x([t], "hidden"), t; }() : null; return { onCreate: function () { i && (r.insertBefore(i, r.firstElementChild), r.setAttribute("data-animatefill", ""), r.style.overflow = "hidden", t.setProps({ arrow: !1, animation: "shift-away" })); }, onMount: function () { if (i) { var t = r.style.transitionDuration, e = Number(t.replace("ms", "")); o.style.transitionDelay = Math.round(e / 10) + "ms", i.style.transitionDuration = t, x([i], "visible"); } }, onShow: function () { i && (i.style.transitionDuration = "0ms"); }, onHide: function () { i && x([i], "hidden"); } }; } }; var q = { clientX: 0, clientY: 0 }, $ = []; function J(t) { var e = t.clientX, n = t.clientY; q = { clientX: e, clientY: n }; } var G = { name: "followCursor", defaultValue: !1, fn: function (t) { var e = t.reference, n = E(t.props.triggerTarget || e), r = !1, o = !1, i = !0, a = t.props; function s() { return "initial" === t.props.followCursor && t.state.isVisible; } function u() { n.addEventListener("mousemove", f); } function p() { n.removeEventListener("mousemove", f); } function c() { r = !0, t.setProps({ getReferenceClientRect: null }), r = !1; } function f(n) { var r = !n.target || e.contains(n.target), o = t.props.followCursor, i = n.clientX, a = n.clientY, s = e.getBoundingClientRect(), u = i - s.left, p = a - s.top; !r && t.props.interactive || t.setProps({ getReferenceClientRect: function () { var t = e.getBoundingClientRect(), n = i, r = a; "initial" === o && (n = t.left + u, r = t.top + p); var s = "horizontal" === o ? t.top : r, c = "vertical" === o ? t.right : n, f = "horizontal" === o ? t.bottom : r, l = "vertical" === o ? t.left : n; return { width: c - l, height: f - s, top: s, right: c, bottom: f, left: l }; } }); } function l() { t.props.followCursor && ($.push({ instance: t, doc: n }), function (t) { t.addEventListener("mousemove", J); }(n)); } function d() { 0 === ($ = $.filter((function (e) { return e.instance !== t; }))).filter((function (t) { return t.doc === n; })).length && function (t) { t.removeEventListener("mousemove", J); }(n); } return { onCreate: l, onDestroy: d, onBeforeUpdate: function () { a = t.props; }, onAfterUpdate: function (e, n) { var i = n.followCursor; r || void 0 !== i && a.followCursor !== i && (d(), i ? (l(), !t.state.isMounted || o || s() || u()) : (p(), c())); }, onMount: function () { t.props.followCursor && !o && (i && (f(q), i = !1), s() || u()); }, onTrigger: function (t, e) { h(e) && (q = { clientX: e.clientX, clientY: e.clientY }), o = "focus" === e.type; }, onHidden: function () { t.props.followCursor && (c(), p(), i = !0); } }; } }; var K = { name: "inlinePositioning", defaultValue: !1, fn: function (t) { var e, n = t.reference; var r = -1, o = !1, i = [], a = { name: "tippyInlinePositioning", enabled: !0, phase: "afterWrite", fn: function (o) { var a = o.state; t.props.inlinePositioning && (-1 !== i.indexOf(a.placement) && (i = []), e !== a.placement && -1 === i.indexOf(a.placement) && (i.push(a.placement), t.setProps({ getReferenceClientRect: function () { return function (t) { return function (t, e, n, r) { if (n.length < 2 || null === t) return e; if (2 === n.length && r >= 0 && n[0].left > n[1].right) return n[r] || e; switch (t) { case "top": case "bottom": var o = n[0], i = n[n.length - 1], a = "top" === t, s = o.top, u = i.bottom, p = a ? o.left : i.left, c = a ? o.right : i.right; return { top: s, bottom: u, left: p, right: c, width: c - p, height: u - s }; case "left": case "right": var f = Math.min.apply(Math, n.map((function (t) { return t.left; }))), l = Math.max.apply(Math, n.map((function (t) { return t.right; }))), d = n.filter((function (e) { return "left" === t ? e.left === f : e.right === l; })), v = d[0].top, m = d[d.length - 1].bottom; return { top: v, bottom: m, left: f, right: l, width: l - f, height: m - v }; default: return e; } }(l(t), n.getBoundingClientRect(), d(n.getClientRects()), r); }(a.placement); } })), e = a.placement); } }; function s() { var e; o || (e = function (t, e) { var n; return { popperOptions: Object.assign({}, t.popperOptions, { modifiers: [].concat(((null == (n = t.popperOptions) ? void 0 : n.modifiers) || []).filter((function (t) { return t.name !== e.name; })), [e]) }) }; }(t.props, a), o = !0, t.setProps(e), o = !1); } return { onCreate: s, onAfterUpdate: s, onTrigger: function (e, n) { if (h(n)) { var o = d(t.reference.getClientRects()), i = o.find((function (t) { return t.left - 2 <= n.clientX && t.right + 2 >= n.clientX && t.top - 2 <= n.clientY && t.bottom + 2 >= n.clientY; })), a = o.indexOf(i); r = a > -1 ? a : r; } }, onHidden: function () { r = -1; } }; } }; var Q = { name: "sticky", defaultValue: !1, fn: function (t) { var e = t.reference, n = t.popper; function r(e) { return !0 === t.props.sticky || t.props.sticky === e; } var o = null, i = null; function a() { var s = r("reference") ? (t.popperInstance ? t.popperInstance.state.elements.reference : e).getBoundingClientRect() : null, u = r("popper") ? n.getBoundingClientRect() : null; (s && Z(o, s) || u && Z(i, u)) && t.popperInstance && t.popperInstance.update(), o = s, i = u, t.state.isMounted && requestAnimationFrame(a); } return { onMount: function () { t.props.sticky && a(); } }; } }; function Z(t, e) { return !t || !e || (t.top !== e.top || t.right !== e.right || t.bottom !== e.bottom || t.left !== e.left); } return e && function (t) { var e = document.createElement("style"); e.textContent = t, e.setAttribute("data-tippy-stylesheet", ""); var n = document.head, r = document.querySelector("head>style,head>link"); r ? n.insertBefore(e, r) : n.appendChild(e); }('.tippy-box[data-animation=fade][data-state=hidden]{opacity:0}[data-tippy-root]{max-width:calc(100vw - 10px)}.tippy-box{position:relative;background-color:#333;color:#fff;border-radius:4px;font-size:14px;line-height:1.4;white-space:normal;outline:0;transition-property:transform,visibility,opacity}.tippy-box[data-placement^=top]>.tippy-arrow{bottom:0}.tippy-box[data-placement^=top]>.tippy-arrow:before{bottom:-7px;left:0;border-width:8px 8px 0;border-top-color:initial;transform-origin:center top}.tippy-box[data-placement^=bottom]>.tippy-arrow{top:0}.tippy-box[data-placement^=bottom]>.tippy-arrow:before{top:-7px;left:0;border-width:0 8px 8px;border-bottom-color:initial;transform-origin:center bottom}.tippy-box[data-placement^=left]>.tippy-arrow{right:0}.tippy-box[data-placement^=left]>.tippy-arrow:before{border-width:8px 0 8px 8px;border-left-color:initial;right:-7px;transform-origin:center left}.tippy-box[data-placement^=right]>.tippy-arrow{left:0}.tippy-box[data-placement^=right]>.tippy-arrow:before{left:-7px;border-width:8px 8px 8px 0;border-right-color:initial;transform-origin:center right}.tippy-box[data-inertia][data-state=visible]{transition-timing-function:cubic-bezier(.54,1.5,.38,1.11)}.tippy-arrow{width:16px;height:16px;color:#333}.tippy-arrow:before{content:"";position:absolute;border-color:transparent;border-style:solid}.tippy-content{position:relative;padding:5px 9px;z-index:1}'), F.setDefaultProps({ plugins: [Y, G, K, Q], render: N }), F.createSingleton = function (t, e) { var n; void 0 === e && (e = {}); var r, o = t, i = [], a = [], s = e.overrides, u = [], f = !1; function l() { a = o.map((function (t) { return c(t.props.triggerTarget || t.reference); })).reduce((function (t, e) { return t.concat(e); }), []); } function d() { i = o.map((function (t) { return t.reference; })); } function v(t) { o.forEach((function (e) { t ? e.enable() : e.disable(); })); } function g(t) { return o.map((function (e) { var n = e.setProps; return e.setProps = function (o) { n(o), e.reference === r && t.setProps(o); }, function () { e.setProps = n; }; })); } function h(t, e) { var n = a.indexOf(e); if (e !== r) { r = e; var u = (s || []).concat("content").reduce((function (t, e) { return t[e] = o[n].props[e], t; }), {}); t.setProps(Object.assign({}, u, { getReferenceClientRect: "function" == typeof u.getReferenceClientRect ? u.getReferenceClientRect : function () { var t; return null == (t = i[n]) ? void 0 : t.getBoundingClientRect(); } })); } } v(!1), d(), l(); var b = { fn: function () { return { onDestroy: function () { v(!0); }, onHidden: function () { r = null; }, onClickOutside: function (t) { t.props.showOnCreate && !f && (f = !0, r = null); }, onShow: function (t) { t.props.showOnCreate && !f && (f = !0, h(t, i[0])); }, onTrigger: function (t, e) { h(t, e.currentTarget); } }; } }, y = F(m(), Object.assign({}, p(e, ["overrides"]), { plugins: [b].concat(e.plugins || []), triggerTarget: a, popperOptions: Object.assign({}, e.popperOptions, { modifiers: [].concat((null == (n = e.popperOptions) ? void 0 : n.modifiers) || [], [W]) }) })), w = y.show; y.show = function (t) { if (w(), !r && null == t) return h(y, i[0]); if (!r || null != t) { if ("number" == typeof t) return i[t] && h(y, i[t]); if (o.indexOf(t) >= 0) { var e = t.reference; return h(y, e); } return i.indexOf(t) >= 0 ? h(y, t) : void 0; } }, y.showNext = function () { var t = i[0]; if (!r) return y.show(0); var e = i.indexOf(r); y.show(i[e + 1] || t); }, y.showPrevious = function () { var t = i[i.length - 1]; if (!r) return y.show(t); var e = i.indexOf(r), n = i[e - 1] || t; y.show(n); }; var x = y.setProps; return y.setProps = function (t) { s = t.overrides || s, x(t); }, y.setInstances = function (t) { v(!0), u.forEach((function (t) { return t(); })), o = t, v(!1), d(), l(), u = g(y), y.setProps({ triggerTarget: a }); }, u = g(y), y; }, F.delegate = function (t, e) { var n = [], o = [], i = !1, a = e.target, s = p(e, ["target"]), u = Object.assign({}, s, { trigger: "manual", touch: !1 }), f = Object.assign({ touch: R.touch }, s, { showOnCreate: !0 }), l = F(t, u); function d(t) { if (t.target && !i) { var n = t.target.closest(a); if (n) { var r = n.getAttribute("data-tippy-trigger") || e.trigger || R.trigger; if (!n._tippy && !("touchstart" === t.type && "boolean" == typeof f.touch || "touchstart" !== t.type && r.indexOf(X[t.type]) < 0)) { var s = F(n, f); s && (o = o.concat(s)); } } } } function v(t, e, r, o) { void 0 === o && (o = !1), t.addEventListener(e, r, o), n.push({ node: t, eventType: e, handler: r, options: o }); } return c(l).forEach((function (t) { var e = t.destroy, a = t.enable, s = t.disable; t.destroy = function (t) { void 0 === t && (t = !0), t && o.forEach((function (t) { t.destroy(); })), o = [], n.forEach((function (t) { var e = t.node, n = t.eventType, r = t.handler, o = t.options; e.removeEventListener(n, r, o); })), n = [], e(); }, t.enable = function () { a(), o.forEach((function (t) { return t.enable(); })), i = !1; }, t.disable = function () { s(), o.forEach((function (t) { return t.disable(); })), i = !0; }, function (t) { var e = t.reference; v(e, "touchstart", d, r), v(e, "mouseover", d), v(e, "focusin", d), v(e, "click", d); }(t); })), l; }, F.hideAll = function (t) { var e = void 0 === t ? {} : t, n = e.exclude, r = e.duration; _.forEach((function (t) { var e = !1; if (n && (e = b(n) ? t.reference === n : t.popper === n.popper), !e) { var o = t.props.duration; t.setProps({ duration: r }), t.hide(), t.state.isDestroyed || t.setProps({ duration: o }); } })); }, F.roundArrow = '<svg width="16" height="6" xmlns="http://www.w3.org/2000/svg"><path d="M0 6s1.796-.013 4.67-3.615C5.851.9 6.93.006 8 0c1.07-.006 2.148.887 3.343 2.385C14.233 6.005 16 6 16 6H0z"></svg>', F; }));
