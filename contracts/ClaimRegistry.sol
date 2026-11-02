// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ClaimRegistry {
    // Mapping from exact fingerprint hash to the insurer who registered it
    mapping(bytes32 => address) public claimHashes;

    // Events to track registrations and duplicates
    event ClaimRegistered(bytes32 indexed claimHash, address indexed insurer);
    event DuplicateAlert(bytes32 indexed claimHash, address indexed submittingInsurer, address indexed originalInsurer);

    /**
     * @dev Registers a new claim hash. If it already exists, alerts the network.
     * @param claimHash The SHA-256 exact match fingerprint of the claim
     */
    function registerClaim(bytes32 claimHash) public {
        address existingInsurer = claimHashes[claimHash];

        if (existingInsurer != address(0)) {
            // Hash already exists! Emit an alert.
            emit DuplicateAlert(claimHash, msg.sender, existingInsurer);
            
            // We revert here if we want to enforce strict non-duplication at contract level,
            // but for tracking purposes, just emitting an event is better so it is logged.
            // revert("Claim duplicate detected"); 
        } else {
            // First time this hash is seen. Store it.
            claimHashes[claimHash] = msg.sender;
            emit ClaimRegistered(claimHash, msg.sender);
        }
    }

    /**
     * @dev Checks if a claim hash is already registered
     * @param claimHash The fingerprint hash
     * @return bool True if registered, False otherwise
     */
    function isRegistered(bytes32 claimHash) public view returns (bool) {
        return claimHashes[claimHash] != address(0);
    }
}
